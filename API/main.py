# -*- coding: utf-8 -*-
 
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
 
 
# =========================
# LOAD ENV VARIABLES
# =========================
 
load_dotenv()
 
 
# =========================
# CONFIGURATION
# =========================
 
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM")
 
MYSQL_URL = "mysql+pymysql://{}:{}@{}:{}/{}".format(
    os.getenv("MYSQL_USER"),
    os.getenv("MYSQL_PASSWORD"),
    os.getenv("MYSQL_HOST"),
    os.getenv("MYSQL_PORT"),
    os.getenv("MYSQL_DATABASE")
)
 
 
# =========================
# DATABASE ENGINE
# =========================
 
engine = create_engine(MYSQL_URL)
 
 
# =========================
# FASTAPI APP
# =========================
 
app = FastAPI(
    title="Traffic & Pollution API",
    description="Big Data Datamarts API — Paris Traffic & Air Quality",
    version="1.0"
)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
# =========================
# JWT AUTH
# =========================
 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
 
 
# =========================
# LOGIN ENDPOINT
# =========================
 
@app.post("/login", tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
 
    if form_data.username != "admin" or form_data.password != "admin123":
        raise HTTPException(status_code=401, detail="Invalid credentials")
 
    token = jwt.encode(
        {"sub": form_data.username},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
 
    return {"access_token": token, "token_type": "bearer"}
 
 
# =========================
# VERIFY TOKEN
# =========================
 
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
 
 
# =========================
# HOME ENDPOINT
# =========================
 
@app.get("/", tags=["Health"])
def home():
    return {"message": "Big Data API Running", "status": "ok"}
 
 
# =====================================================
# DATAMART 1 — MOST POLLUTED ZONES
# =====================================================
 
@app.get("/pollution", tags=["Pollution"])
def get_pollution(
    page:  int = Query(1,  ge=1),
    limit: int = Query(20, ge=1, le=100),
    zone:  str = Query(None, description="Filter by zone name"),
    token: dict = Depends(verify_token)
):
    offset     = (page - 1) * limit
    zone_filter = "AND zone = :zone" if zone else ""
 
    query = text(f"""
        SELECT zone, year, month, day,
               avg_pollution, max_pollution, avg_aqi
        FROM datamart_pollution
        WHERE 1=1 {zone_filter}
        ORDER BY avg_pollution DESC
        LIMIT :limit OFFSET :offset
    """)
 
    with engine.connect() as conn:
        result = conn.execute(query, {"limit": limit, "offset": offset, **({"zone": zone} if zone else {})})
        data   = [dict(row) for row in result.mappings()]
 
    return {"page": page, "limit": limit, "total": len(data), "data": data}
 
 
@app.get("/pollution/summary", tags=["Pollution"])
def get_pollution_summary(token: dict = Depends(verify_token)):
    """Average pollution per zone — ideal for bar charts."""
    query = text("""
        SELECT zone,
               ROUND(AVG(avg_pollution), 2) AS avg_pollution,
               ROUND(MAX(max_pollution), 2) AS max_pollution,
               ROUND(AVG(avg_aqi), 2)       AS avg_aqi
        FROM datamart_pollution
        GROUP BY zone
        ORDER BY avg_pollution DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        data   = [dict(row) for row in result.mappings()]
    return {"data": data}
 
 
# =====================================================
# DATAMART 2 — MOST CONGESTED HOURS
# =====================================================
 
@app.get("/traffic", tags=["Traffic"])
def get_traffic(
    page:  int = Query(1,  ge=1),
    limit: int = Query(20, ge=1, le=200),
    zone:  str = Query(None, description="Filter by zone name"),
    hour:  int = Query(None, ge=0, le=23, description="Filter by hour"),
    token: dict = Depends(verify_token)
):
    offset      = (page - 1) * limit
    filters     = []
    params      = {"limit": limit, "offset": offset}
 
    if zone:
        filters.append("zone = :zone")
        params["zone"] = zone
    if hour is not None:
        filters.append("hour = :hour")
        params["hour"] = hour
 
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
 
    query = text(f"""
        SELECT zone, hour, year, month, day,
               avg_traffic, max_traffic
        FROM datamart_traffic
        {where}
        ORDER BY avg_traffic DESC
        LIMIT :limit OFFSET :offset
    """)
 
    with engine.connect() as conn:
        result = conn.execute(query, params)
        data   = [dict(row) for row in result.mappings()]
 
    return {"page": page, "limit": limit, "total": len(data), "data": data}
 
 
@app.get("/traffic/by-hour", tags=["Traffic"])
def get_traffic_by_hour(token: dict = Depends(verify_token)):
    """Average traffic per hour across all zones — ideal for line charts."""
    query = text("""
        SELECT hour,
               ROUND(AVG(avg_traffic), 2) AS avg_traffic,
               ROUND(MAX(max_traffic), 2) AS max_traffic
        FROM datamart_traffic
        GROUP BY hour
        ORDER BY hour ASC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        data   = [dict(row) for row in result.mappings()]
    return {"data": data}
 
 
@app.get("/traffic/by-zone", tags=["Traffic"])
def get_traffic_by_zone(token: dict = Depends(verify_token)):
    """Average traffic per zone — ideal for bar charts."""
    query = text("""
        SELECT zone,
               ROUND(AVG(avg_traffic), 2) AS avg_traffic,
               ROUND(MAX(max_traffic), 2) AS max_traffic
        FROM datamart_traffic
        GROUP BY zone
        ORDER BY avg_traffic DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        data   = [dict(row) for row in result.mappings()]
    return {"data": data}
 
 
@app.get("/traffic/heatmap", tags=["Traffic"])
def get_traffic_heatmap(token: dict = Depends(verify_token)):
    """Traffic per zone per hour — ideal for heatmaps."""
    query = text("""
        SELECT zone, hour,
               ROUND(AVG(avg_traffic), 2) AS avg_traffic
        FROM datamart_traffic
        GROUP BY zone, hour
        ORDER BY zone, hour
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        data   = [dict(row) for row in result.mappings()]
    return {"data": data}
 
 
# =====================================================
# DATAMART 3 — TRAFFIC VS POLLUTION
# =====================================================
 
@app.get("/traffic-pollution", tags=["Traffic vs Pollution"])
def get_traffic_pollution(
    page:          int = Query(1,  ge=1),
    limit:         int = Query(20, ge=1, le=200),
    traffic_level: str = Query(None, description="Low Traffic | Medium Traffic | High Traffic"),
    zone:          str = Query(None),
    token:         dict = Depends(verify_token)
):
    offset  = (page - 1) * limit
    filters = []
    params  = {"limit": limit, "offset": offset}
 
    if zone:
        filters.append("zone = :zone")
        params["zone"] = zone
    if traffic_level:
        filters.append("traffic_level = :traffic_level")
        params["traffic_level"] = traffic_level
 
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
 
    query = text(f"""
        SELECT zone, hour, year, month, day,
               avg_pollution, avg_traffic,
               avg_temperature, avg_humidity,
               traffic_level
        FROM datamart_traffic_pollution
        {where}
        ORDER BY avg_traffic DESC
        LIMIT :limit OFFSET :offset
    """)
 
    with engine.connect() as conn:
        result = conn.execute(query, params)
        data   = [dict(row) for row in result.mappings()]
 
    return {"page": page, "limit": limit, "total": len(data), "data": data}
 
 
@app.get("/traffic-pollution/summary", tags=["Traffic vs Pollution"])
def get_traffic_pollution_summary(token: dict = Depends(verify_token)):
    """Per-zone summary of traffic vs pollution — ideal for scatter/bubble charts."""
    query = text("""
        SELECT zone,
               ROUND(AVG(avg_traffic), 2)     AS avg_traffic,
               ROUND(AVG(avg_pollution), 2)   AS avg_pollution,
               ROUND(AVG(avg_temperature), 2) AS avg_temperature,
               ROUND(AVG(avg_humidity), 2)    AS avg_humidity
        FROM datamart_traffic_pollution
        GROUP BY zone
        ORDER BY avg_traffic DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        data   = [dict(row) for row in result.mappings()]
    return {"data": data}
 
 
@app.get("/traffic-pollution/by-level", tags=["Traffic vs Pollution"])
def get_by_traffic_level(token: dict = Depends(verify_token)):
    """Pollution stats grouped by traffic level."""
    query = text("""
        SELECT traffic_level,
               COUNT(*)                        AS count,
               ROUND(AVG(avg_pollution), 2)   AS avg_pollution,
               ROUND(AVG(avg_temperature), 2) AS avg_temperature,
               ROUND(AVG(avg_humidity), 2)    AS avg_humidity
        FROM datamart_traffic_pollution
        GROUP BY traffic_level
        ORDER BY avg_pollution DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        data   = [dict(row) for row in result.mappings()]
    return {"data": data}
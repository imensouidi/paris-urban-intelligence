# README — Plateforme Big Data basée sur une Architecture Médaillon

## 📌 Présentation du projet

Ce projet a pour objectif de concevoir une **plateforme Big Data complète** basée sur une **architecture médaillon** permettant :

* l’ingestion de données Open Data,
* leur nettoyage et validation,
* la création de datamarts analytiques,
* leur exploitation via une API REST sécurisée,
* et leur visualisation via un dashboard interactif.

Le projet repose sur les technologies Big Data suivantes :

* Apache Spark
* HDFS
* Hive
* MySQL
* FastAPI
* Streamlit
* Docker

---

# 🎯 Problématique métier

L’objectif métier choisi est :

## **Analyser l’impact du trafic routier sur la pollution atmosphérique à Paris**

Le projet permet de répondre à plusieurs problématiques :

1. Quelles sont les zones les plus polluées ?
2. Quelles sont les heures les plus congestionnées ?
3. Existe-t-il une corrélation entre trafic routier et pollution ?

---

# 📂 Sources de données

## 1. Données qualité de l’air

Les données de qualité de l’air proviennent de la plateforme OpenAQ.

Elles contiennent notamment :

* indice de qualité de l’air,
* niveau de pollution,
* température,
* humidité,
* zones géographiques.

Les données ont été intégrées dans MySQL avant ingestion dans la plateforme Big Data.
Le volume total est **120 000 lignes**.

---

## 2. Données trafic routier

Les données de trafic routier proviennent de l’Open Data Paris :

[Open Data Paris – Comptages Routiers Permanents](https://opendata.paris.fr/explore/dataset/comptages-routiers-permanents/export/?utm_source=chatgpt.com)

Ces données contiennent :

* les mesures de trafic,
* le débit horaire,
* les états du trafic,
* les zones routières de Paris.

Le volume total est **200 000 lignes**.

---

# 🏗 Architecture du projet

```text
Open Data Sources
        ↓
feeder.py
        ↓
RAW Layer (HDFS)
        ↓
processor.py
        ↓
SILVER Layer (Hive)
        ↓
datamart.py
        ↓
Gold Layer (MySQL)
        ↓
API REST FastAPI (JWT)
        ↓
Dashboard Streamlit
```

---

# ⚙ Technologies utilisées

| Technologie  | Rôle                   |
| ------------ | ---------------------- |
| Apache Spark | Traitement distribué   |
| HDFS         | Data Lake RAW          |
| Hive         | Couche SILVER          |
| MySQL        | Datamarts GOLD         |
| FastAPI      | API REST               |
| Streamlit    | Dashboard              |
| Docker       | Conteneurisation       |
| PySpark      | Développement Big Data |
| JWT          | Sécurisation API       |

---

# 📁 Structure du projet

```text
# 📁 Structure du projet

bigdata-projet/
│
├── API/
│   ├── .env
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── dashboard/
│   ├── .env
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── pipeline/
│   ├── feeder.py
│   ├── processor.py
│   └── datamart.py
│
├── source/
│   ├── trafic_routier.csv
│   └── paris_air_quality.csv
│
├── docker-compose.yml
├── hadoop.env
├── hadoop-hive.env
├── hive-site.xml
├── mariadb-java-client-2.x.x.jar
│
└── readme.md
```

---

# 🚀 Étape 1 — Ingestion des données (`feeder.py`)

## Objectif

Le script `feeder.py` permet l’ingestion des données brutes dans HDFS.

## Fonctionnement

Le script :

* lit les fichiers CSV Open Data,
* ajoute les colonnes de partitionnement,
* écrit les données dans HDFS,
* partitionne les données par date d’ingestion.

---

## Partitionnement RAW

Les données RAW sont partitionnées selon :

```text
year=YYYY/month=MM/day=DD
```

---

## Paramétrage Spark

Le script `feeder.py` est exécuté avec Apache Spark en mode cluster standalone via la commande suivante :

```bash
/spark/bin/spark-submit \
--master spark://spark-master:7077 \
--deploy-mode client \
--executor-cores 1 \
--total-executor-cores 1 \
--executor-memory 1g \
--driver-memory 1g \
--jars /spark/jars/mariadb-java-client-2.7.3.jar \
/opt/pipeline/feeder.py \
--traffic_input file:///source/trafic_routier.csv \
--output_traffic hdfs://namenode:9000/data/raw/traffic/traffic_partitioned \
--output_air hdfs://namenode:9000/data/raw/air_quality/air_quality_partitioned \
--mysql_host mysql \
--mysql_port 3306 \
--mysql_database air_quality_db \
--mysql_table paris_air_quality \
--mysql_user root \
--mysql_password root
```

Cette étape permet :
- l’ingestion des données de trafic routier,
- la récupération des données de qualité de l’air depuis MariaDB,
- le partitionnement des données,
- le stockage des données brutes dans HDFS (couche Bronze).

---

## Logs

Le script génère des logs :

* `log.info`
* `log.error`

exportés dans des fichiers `.txt`.

---

# 🧹 Étape 2 — Traitement des données (`processor.py`)

## Objectif

Transformer les données RAW en données propres et exploitables dans la couche SILVER.

---

# ✔ Validations effectuées

Le processor applique plusieurs règles de validation :

1. suppression des valeurs nulles,
2. suppression des doublons,
3. validation des valeurs de pollution,
4. validation des températures,
5. validation de l’humidité.

---

# ✔ Jointures

Le projet effectue des jointures entre :

* les données trafic,
* les données pollution.

Les jointures sont réalisées sur :

* la zone,
* l’heure.

---

# ✔ Agrégations

Le projet utilise plusieurs agrégations :

* moyenne du trafic,
* moyenne de pollution,
* température moyenne,
* humidité moyenne.

---

# ✔ Window Functions

Le projet utilise des window functions Spark avec :

```sql
PARTITION BY zone
```

afin d’effectuer des analyses analytiques avancées.

---

# ✔ Optimisation Spark

Le projet démontre l’utilisation de :

```python
cache()
persist()
```

visible dans la Spark UI.

---

# ✔ Écriture SILVER

Les données SILVER sont :

* stockées dans Hive,
* au format Parquet,
* partitionnées par date d’ingestion.

## Traitement des données avec Spark

Le script `processor.py` est exécuté avec Apache Spark afin de nettoyer, transformer et consolider les données issues de la couche Bronze vers la couche Silver.

```bash
/spark/bin/spark-submit \
--master spark://spark-master:7077 \
--deploy-mode client \
--executor-cores 1 \
--total-executor-cores 1 \
--executor-memory 1g \
--driver-memory 1g \
/opt/pipeline/processor.py \
--air_input hdfs://namenode:9000/data/raw/air_quality/air_quality_partitioned \
--traffic_input hdfs://namenode:9000/data/raw/traffic/traffic_partitioned \
--silver_output hdfs://namenode:9000/data/silver/air_traffic_silver
```

Cette étape permet :
- le nettoyage des données,
- la gestion des valeurs manquantes,
- la transformation des colonnes,
- la fusion des données de trafic et de qualité de l’air,
- la génération de la couche Silver dans HDFS.

---

##  Connexion à Hive

Accès au conteneur Hive :

```bash
docker exec -it hive-server bash
```

Connexion à Hive via Beeline :

```bash
beeline -u jdbc:hive2://localhost:10000 -n root
```

Cette étape permet :
- d’interroger les datasets stockés dans Hive,
- de valider les données générées par le pipeline,
- d’exécuter des requêtes analytiques sur les couches Silver et Gold.

---

# 🗄 Étape 3 — Création des Datamarts (`datamart.py`)

## Objectif

Créer des datamarts analytiques à partir de la couche SILVER.

---

# Datamarts créés

## 1. `datamart_pollution`

Analyse des zones les plus polluées.

---

## 2. `datamart_traffic`

Analyse des heures les plus congestionnées.

---

## 3. `datamart_traffic_pollution`

Analyse de la relation entre trafic et pollution.

---

# ✔ Stockage GOLD

Les datamarts sont stockés dans MySQL :

```text
gold_db
```

##  Création des datamarts analytiques avec Spark

Le script `datamart.py` est exécuté avec Apache Spark afin de générer les tables analytiques de la couche Gold à partir des données Silver stockées dans Hive.

```bash
/spark/bin/spark-submit \
--master spark://spark-master:7077 \
--deploy-mode client \
--executor-cores 2 \
--total-executor-cores 4 \
--executor-memory 1g \
--driver-memory 1g \
--conf spark.sql.shuffle.partitions=2 \
--conf spark.hadoop.hive.metastore.uris=thrift://hive-metastore:9083 \
--jars spark/jars/mariadb-java-client-2.7.3.jar \
/opt/pipeline/datamart.py \
--hive_table silver_db.air_traffic_silver \
--mysql_url "jdbc:mysql://mysql:3306/gold_db?allowPublicKeyRetrieval=true&useSSL=false" \
--mysql_user root \
--mysql_password root \
--mysql_driver org.mariadb.jdbc.Driver
```

Cette étape permet :
- la lecture des données Silver depuis Hive,
- la création des agrégations analytiques,
- la génération des datamarts de la couche Gold,
- le stockage des résultats dans MariaDB,
- l’exploitation des données par l’API et le dashboard.

---

# 🔐 Étape 4 — API REST sécurisée (`FastAPI`)

## Objectif

Exposer les datamarts analytiques via une API REST sécurisée afin de permettre l’accès aux données de trafic et de pollution.

---

# Fonctionnalités de l’API

L’API implémente :

- authentification JWT,
- sécurisation OAuth2,
- pagination des résultats,
- filtres dynamiques,
- connexion MariaDB/MySQL,
- endpoints REST analytiques,
- documentation Swagger automatique.

:contentReference[oaicite:0]{index=0}

---

# Endpoints disponibles

| Endpoint                          | Description |
|----------------------------------|-------------|
| `/login`                         | Authentification JWT |
| `/`                              | Vérification de l’état de l’API |
| `/pollution`                     | Données pollution avec pagination |
| `/pollution/summary`             | Résumé pollution par zone |
| `/traffic`                       | Données trafic avec filtres |
| `/traffic/by-hour`               | Trafic moyen par heure |
| `/traffic/by-zone`               | Trafic moyen par zone |
| `/traffic/heatmap`               | Données pour heatmap trafic |
| `/traffic-pollution`             | Corrélation trafic/pollution |
| `/traffic-pollution/summary`     | Résumé analytique par zone |
| `/traffic-pollution/by-level`    | Pollution par niveau de trafic |

:contentReference[oaicite:1]{index=1}

---

# ✔ Sécurité JWT

L’API utilise :

```text
Bearer Token
```

pour sécuriser l’accès aux endpoints analytiques.

L’authentification est réalisée via OAuth2 et JWT.

---

# ✔ Documentation Swagger

Documentation interactive disponible sur :

```text
http://localhost:8000/docs
```

---

# 📊 Étape 5 — Dashboard de visualisation (`Streamlit`)

## Objectif

Visualiser les datamarts analytiques à travers un dashboard interactif dédié à l’analyse du trafic routier et de la qualité de l’air à Paris.

---

# Fonctionnalités du dashboard

Le dashboard permet :

- la visualisation interactive des indicateurs,
- le filtrage dynamique par zone,
- le filtrage par plage horaire,
- l’analyse des niveaux de trafic,
- l’exploration des corrélations trafic/pollution.

:contentReference[oaicite:2]{index=2}

---

# ✔ KPIs affichés

Le dashboard affiche notamment :

- la zone la plus polluée,
- la zone la plus congestionnée,
- l’heure de trafic maximale,
- l’indice moyen de pollution,
- la zone la moins polluée.

:contentReference[oaicite:3]{index=3}

---

# ✔ Visualisations disponibles

## 🌫 Qualité de l’air

- pollution moyenne par zone,
- répartition de la pollution,
- comparaison AQI / pollution.

---

## 🚗 Analyse du trafic

- trafic moyen par zone,
- évolution du trafic par heure,
- heatmap trafic (zone × heure).

---

## 📊 Corrélation trafic / pollution

- scatter plot trafic vs pollution,
- analyse par niveau de trafic,
- indicateurs météo (température et humidité).

:contentReference[oaicite:4]{index=4}

---

# ✔ Technologies utilisées

- FastAPI
- Streamlit
- Plotly
- SQLAlchemy
- MariaDB/MySQL
- JWT / OAuth2

---

# ✔ URL Dashboard

```text
http://localhost:8501
```

---

# 🐳 Conteneurisation Docker

L’ensemble du projet est conteneurisé avec Docker :

* Spark
* Hive
* HDFS
* MySQL
* API
* Dashboard

---

# 📈 Résultats obtenus

Le projet répond aux exigences demandées :

✅ Architecture médaillon
✅ Ingestion Open Data
✅ Partitionnement RAW/SILVER
✅ Validation des données
✅ Jointures
✅ Agrégations
✅ Window Functions
✅ Optimisation Spark
✅ Datamarts relationnels
✅ API REST sécurisée JWT
✅ Pagination
✅ Dashboard interactif
✅ Dockerisation complète

---

# ✅ Conclusion

Ce projet démontre la mise en place d’une plateforme Data Engineering complète basée sur les technologies Big Data modernes.

Les données Open Data sont :

* ingérées,
* nettoyées,
* transformées,
* analysées,
* exposées via API,
* puis visualisées dans un dashboard interactif.

L’architecture mise en place permet une séparation claire entre :

* données brutes (RAW),
* données nettoyées (SILVER),
* données analytiques (GOLD),

suivant le principe de l’architecture médaillon.

# acasa-pyapp
h1 Architecture

- Main chord: Embedded SQLite3 database + ASGI web framework (Quart)
- Concurrent: Event-driven architecture using message middleare (Kafka?, Redis?) and "big data" NoSQL store (MonetDB)

h2 Requirements
- Python 3.9
# acasa-pyapp
<p> Example application using primarily Pathon constructs

<h3> Architecture </h3>

- Main chord: Embedded SQLite3 database + ASGI web framework (Quart)
- Concurrent: Event-driven architecture using message middleare (Kafka?, Redis?) and "big data" NoSQL store (MonetDB)

<h3> Requirements </h3>
- Python 3.9
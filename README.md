# acasa-pyapp
<p> Example application using primarily Python constructs

<h3> Architecture </h3>

- Main chord: Embedded SQLite3 database + ASGI web framework (Quart) [Separate RESTful web services]
- Concurrent: Event-driven architecture using message middleare (Kafka?, Redis?) and "big data" NoSQL store (MonetDB)

<h3> Requirements </h3>
- Python 3.9
- Quart 0.18.3
- ArangoClient 7.5.6
- MonetDB(e) 0.11
- SQLite 3.40.1
- wxPython 4.2.0

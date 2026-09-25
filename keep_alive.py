import logging
import os
import threading

from flask import Flask, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)

mongo_client = None
mongo_database = None
mongo_error = None


def connect_mongodb():
    """Connect to MongoDB when a Render environment variable is configured."""
    global mongo_client, mongo_database, mongo_error

    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
    database_name = os.getenv("MONGODB_DATABASE", "kingdom_of_thailand")

    if not mongo_uri:
        mongo_error = "MONGODB_URI is not configured"
        logging.warning(mongo_error)
        return None

    try:
        mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        mongo_client.admin.command("ping")
        mongo_database = mongo_client[database_name]
        mongo_error = None
        logging.info("Connected to MongoDB database '%s'", database_name)
        return mongo_database
    except PyMongoError as error:
        mongo_error = str(error)
        logging.exception("Could not connect to MongoDB")
        return None


def get_database():
    """Return the active MongoDB database for other modules."""
    return mongo_database


@app.get("/")
def health_check():
    return jsonify({"status": "ok", "service": "kingdom-of-thailand-bot"})


@app.get("/health")
def health_status():
    if mongo_database is None:
        return jsonify({"status": "degraded", "mongodb": "disconnected", "error": mongo_error}), 503

    try:
        mongo_client.admin.command("ping")
        return jsonify({"status": "ok", "mongodb": "connected"})
    except PyMongoError as error:
        return jsonify({"status": "degraded", "mongodb": "disconnected", "error": str(error)}), 503


def start_keep_alive():
    """Start Render's HTTP health server without blocking the Discord bot."""
    connect_mongodb()
    port = int(os.getenv("PORT", "10000"))
    server_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, use_reloader=False),
        daemon=True,
    )
    server_thread.start()
    logging.info("Keep-alive server started on port %s", port)

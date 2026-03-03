from prometheus_client import Counter, Histogram

PREDICTIONS_TOTAL = Counter(
    "predictions_total",
    "Total number of ML predictions",
    ["result"],
)

PREDICTION_DURATION_SECONDS = Histogram(
    "prediction_duration_seconds",
    "Time spent on ML model inference (seconds)",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

PREDICTION_ERRORS_TOTAL = Counter(
    "prediction_errors_total",
    "Total number of prediction errors",
    ["error_type"],
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Time spent executing PostgreSQL queries (seconds)",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

MODEL_PREDICTION_PROBABILITY = Histogram(
    "model_prediction_probability",
    "Distribution of violation probabilities produced by the ML model",
    buckets=[0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
)


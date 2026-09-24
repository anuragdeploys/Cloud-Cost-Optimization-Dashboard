cat > README.md <<'EOF'
# Cloud Cost Optimization Dashboard

A Python-based cloud cost monitoring and optimization dashboard that collects,
stores, analyzes, and exposes cloud cost data through a REST API and web
dashboard.

The project is designed with a low-cost development approach using sample
data and mocked AWS interactions for testing. Real AWS Cost Explorer
collection is optional and disabled by default.

---

## Project Overview

The Cloud Cost Optimization Dashboard provides a simple platform for:

- Collecting cloud cost data
- Validating cost records
- Storing cost records in SQLite
- Calculating total cloud cost
- Analyzing cost by service
- Analyzing daily cost trends
- Identifying service cost concentration
- Exposing cost information through REST APIs
- Running scheduled cost collection
- Collecting AWS Cost Explorer data when explicitly enabled
- Running the application inside Docker
- Automatically testing the project with GitHub Actions

---

## Architecture

```text
                    AWS Cost Data
                         |
                         v
                AWS Cost Collector
                         |
                         v
                 Cost Normalization
                         |
                         v
                  SQLite Database
                         |
              +----------+----------+
              |                     |
              v                     v
        Cost Analysis          REST API
              |                     |
              +----------+----------+
                         |
                         v
                    Web Dashboard

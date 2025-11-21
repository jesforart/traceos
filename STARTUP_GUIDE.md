# TraceOS v2.0 - Quick Startup Guide

## Start All Services
```bash
cd ~/traceos
docker compose up -d
```

## Check Status
```bash
docker compose ps
```

## Health Checks
```bash
curl http://localhost:8000/v1/health  # TraceMemory
curl http://localhost:8787/v1/health  # Trace
curl http://localhost:8888/v1/health  # Orchestrator
```

## View Logs
```bash
docker compose logs -f              # All services
docker compose logs -f tracememory  # Specific service
```

## Stop Services
```bash
docker compose down
```

## Rebuild After Changes
```bash
docker compose build [service]
docker compose up -d
```

That's it! 🎉

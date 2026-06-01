docker exec -it slh-postgres psql -U postgres -d slh_main -c "SELECT * FROM system_events ORDER BY created_at DESC LIMIT 50;"

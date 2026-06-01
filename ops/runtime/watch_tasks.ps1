docker exec -it slh-postgres psql -U postgres -d slh_main -c "SELECT * FROM bot_tasks ORDER BY id DESC LIMIT 20;"

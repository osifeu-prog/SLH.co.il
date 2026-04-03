param()
$ErrorActionPreference = "Stop"
docker exec slh_redis redis-cli XINFO STREAM slh:updates
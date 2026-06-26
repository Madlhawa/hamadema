import subprocess

cmd = [
    'ssh',
    'root@168.144.28.96',
    'docker exec postgres_db psql -U scraper_user -d lanka_aggregator -c "ALTER USER scraper_user WITH PASSWORD \'Z6hXVzbAf8a5nNQVU5rc\';"'
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)

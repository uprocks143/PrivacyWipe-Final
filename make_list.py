import requests
import zipfile
import io

print("Downloading Top 1 Million sites list...")
url = "http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"
r = requests.get(url)
z = zipfile.ZipFile(io.BytesIO(r.content))

# Pehli 2,00,000 sites nikalna
with z.open('top-1m.csv') as f:
    sites = []
    for i, line in enumerate(f):
        if i >= 200000: break
        # CSV format: rank,domain
        domain = line.decode().strip().split(',')[1]
        sites.append(domain)

with open('sites.txt', 'w') as f:
    f.write('\n'.join(sites))

print("Done! sites.txt with 200,000 domains is ready.")

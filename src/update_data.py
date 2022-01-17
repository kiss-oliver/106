import json
import pandas as pd
import requests as re
import sys
from bs4 import BeautifulSoup
from tqdm import tqdm

# Set up openssl to work with valasztas.hu
re.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
try:
    re.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

# Get config json
config = re.get('https://vtr.valasztas.hu/ogy2022/data/config.json').json()

# Check if version is new
versions = open('../data/versions.txt','r').read().split('\n')
if config['ver'] in versions:
    print('Version {} already collected. Exiting.'.format(config['ver']))
    sys.exit()

# Get Settlement data
data = re.get('https://vtr.valasztas.hu/ogy2022/data/{}/ver/Telepulesek.json'.format(config['ver'])).json()
parsed = [[{y[0]:y[1] for y in x.items() if y[0] not in ['evk_lst','letszam']}|x['letszam']|{'evk':z}
          for z in x['evk_lst']] for x in data['list']]
compiled = [y for x in parsed for y in x]
current = pd.DataFrame(compiled)
current['version'] = config['ver']

# Append to existing data
try:
    past = pd.read_csv('../data/telepules.csv')
    pd.concat([past, current]).to_csv('../data/telepules.csv', index=False)
except FileNotFoundError:
    current.to_csv('../data/telepules.csv', index=False)

# Get szavazokor data
alldata = []
szavazokorok = current[['maz','taz']].drop_duplicates(keep='first')
for codes in tqdm(list(zip(szavazokorok.maz.astype(str).tolist(),szavazokorok.taz.astype(str).tolist())), "Collecting szavazokor data"):
    url = 'https://vtr.valasztas.hu/ogy2022/data/{}/ver/{}/Szavazokorok-{}-{}.json'.format(
           config['ver'],codes[0],codes[0],codes[1])
    data = re.get(url).json()
    for szk in data['data']['szavazokorok']:
        alldata.append({y[0]:y[1] for y in szk.items() if y[0] not in ['letszam']}|szk['letszam']|{'maz':codes[0],'taz':codes[1]})

current = pd.DataFrame(alldata)
current['version'] = config['ver']

# Append to existing data
try:
    past = pd.read_csv('../data/szavazokor.csv')
    pd.concat([past, current]).to_csv('../data/szavazokor.csv', index=False)
except FileNotFoundError:
    current.to_csv('../data/szavazokor.csv', index=False)

# Get OEVK data
data = re.get('https://vtr.valasztas.hu/ogy2022/data/{}/ver/OevkAdatok.json'.format(config['ver'])).json()
parsed = [{y[0]:y[1] for y in x.items() if y[0] not in ['letszam']}|x['letszam'] for x in data['list']]
current = pd.DataFrame(parsed)
current['version'] = config['ver']

# Append to existing data
try:
    past = pd.read_csv('../data/oevk.csv')
    pd.concat([past, current]).to_csv('../data/oevk.csv', index=False)
except FileNotFoundError:
    current.to_csv('../data/oevk.csv', index=False)


# Get osszletszam
data = re.get('https://vtr.valasztas.hu/ogy2022/data/{}/ver/OsszLetszam.json'.format(config['ver'])).json()
current = pd.DataFrame([data['data']])
current['version'] = config['ver']

# Append to existing data
try:
    past = pd.read_csv('../data/summary.csv')
    pd.concat([past, current]).to_csv('../data/summary.csv', index=False)
except FileNotFoundError:
    current.to_csv('../data/summary.csv', index=False)

open('../data/versions.txt','a').write(config['ver'])

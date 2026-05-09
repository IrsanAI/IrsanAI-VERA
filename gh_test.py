import requests

token = None
with open('.env') as f:
    for line in f:
        if line.startswith('GITHUB_TOKEN='):
            token = line.split('=', 1)[1].strip()
            break

print('Token:', (token[:12] + '...') if token else 'MISSING')
print()

headers = {
    'Authorization': 'Bearer ' + token,
    'Accept': 'application/vnd.github+json'
}

queries = ['UAP', 'UFO disclosure', 'FOIA documents', 'UAP FOIA', 'richgel999']
for q in queries:
    r = requests.get(
        'https://api.github.com/search/repositories',
        params={'q': q, 'per_page': 3},
        headers=headers,
        timeout=10
    )
    data = r.json()
    count = data.get('total_count', 'ERROR')
    print('Query [' + q + ']: ' + str(count) + ' results, status=' + str(r.status_code))
    if data.get('items'):
        for item in data['items'][:2]:
            print('  -> ' + item.get('full_name', '') + ' (' + str(item.get('stargazers_count', 0)) + ' stars)')
    print()

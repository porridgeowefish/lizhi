import httpx, asyncio, json

async def main():
    async with httpx.AsyncClient(base_url='http://106.52.9.231:8001', timeout=15) as client:
        r = await client.post('/api/v1/wx/auth/login', data={'username': 'admin', 'password': 'werss2024'})
        token = r.json()['data']['access_token']
        h = {'Authorization': f'Bearer {token}'}

        # Try common WeRSS endpoints
        endpoints = [
            ('GET', '/api/v1/wx/mps'),
            ('GET', '/api/v1/wx/sync'),
            ('POST', '/api/v1/wx/sync'),
            ('GET', '/api/v1/wx/config'),
            ('POST', '/api/v1/wx/config'),
            ('GET', '/api/v1/wx/settings'),
            ('GET', '/api/v1/wx/tasks'),
            ('GET', '/api/v1/wx/feeds'),
            ('GET', '/api/v1/wx/status'),
            ('GET', '/api/v1/wx/cron'),
            ('POST', '/api/v1/wx/refresh'),
            ('GET', '/api/v1/wx/refresh'),
            ('POST', '/api/v1/wx/crawl'),
            ('POST', '/api/v1/wx/sync/all'),
            ('GET', '/api/v1/wx/sync/status'),
            ('GET', '/api/v1/config'),
            ('GET', '/api/v1/settings'),
            ('GET', '/api/v1/sync'),
            ('GET', '/api/v1/tasks'),
            ('POST', '/api/v1/sync/now'),
        ]

        for method, path in endpoints:
            try:
                if method == 'GET':
                    r = await client.get(path, headers=h, timeout=10)
                else:
                    r = await client.post(path, headers=h, timeout=10)
                if r.status_code != 404:
                    body = r.text[:200]
                    print(f"  {method} {path} -> {r.status_code}: {body}")
            except Exception as e:
                print(f"  {method} {path} -> ERROR: {e}")

asyncio.run(main())

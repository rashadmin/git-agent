import requests

ACCESS_TOKEN = "EAAWHm4qbgT4BPWlsqUvh8XrGKnQbDhVVWUCbyIaQtGInT8zt9cs926J4i6mhTM4kL9lSBzULB56OOth2qpgpx5kpzmYqs7zZCTZBILrJMonH7BjMZCgJru2WzuM1ZCZB3g1hLiqhN9Gkb8YEgrsqZAcEhi6FBMijIIa9Xvngel5Oyl4ThWu8jZBpUZAWE5zZB4xm2JFUv90UFVaICLwPnvF7H47twrNlZBt3qlY0ioDRPYgnSZA5YtxOQIbP5aLaroxlfFyWrWy7ePv1LhE3EOZB8AZDZD"

url = "https://graph.facebook.com/v20.0/me/feed"
params = {
    "message": "Hello Facebook! 🚀",
    "access_token": ACCESS_TOKEN
}

r = requests.post(url, data=params)
print(r.status_code, r.json())



from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import user,posts, errors, tokens



# GET	/api/users/<id>	Return a user.
# GET	/api/users	Return the collection of all users.
# GET	/api/users/<id>/followers	Return the followers of this user.
# GET	/api/users/<id>/followed	Return the users this user is following.
# POST	/api/users	Register a new user account.
# PUT	/api/users/<id>	Modify a user.

# Thought for 2sFound API endpoint usageBased on my search through the codebase, here are all the file paths where the API endpoints are used:

# ## Client-side API calls (Frontend):

# 1. **`app/page.tsx`** - Line 85

# 1. Fetches posts: `GET /api/posts` with query parameters



# 2. **`app/users/[id]/page.tsx`** - Lines 51, 62

# 1. Fetches user profile: `GET /api/users/${userId}`
# 2. Fetches user posts: `GET /api/users/${userId}/posts`





# ## API Route Handlers (Backend Proxy):

# 3. **`app/api/posts/route.ts`** - Line 17

# 1. Proxies `GET` requests to Flask backend



# 4. **`app/api/posts/[id]/route.ts`** - Lines 8, 31

# 1. Proxies `GET` and `PUT` requests for individual posts



# 5. **`app/api/users/[id]/route.ts`** - Lines 8, 31

# 1. Proxies `GET` and `PUT` requests for user profiles



# 6. **`app/api/users/[id]/posts/route.ts`** - Line 17

# 1. Proxies `GET` requests for user-specific posts





# All these files act as Next.js API routes that proxy requests to your Flask backend running on `http://127.0.0.1:5000`, handling the communication between your frontend and the actual API endpoints you specified.
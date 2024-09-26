# Social Media API

> RESTful API for a social media platform written in DRF 

## Description

The API allows users to:
- register with their email and password to create an account,
- login with their credentials and receive a token for authentication,
- logout and invalidate their refresh token,
- create and update their profile, including profile picture,
- retrieve their own profile and view profiles of other users,
- search for users by nickname, first_name or last_name fields, 
- follow and unfollow other users,
- view the list of users they are following and the list of users following them,
- create new posts with text content and media attachments (e.g., images),
- retrieve their own posts and posts of users they are following,
- retrieve posts by hashtags,
- like and unlike posts,
- view the list of posts they have liked,
- add comments to posts and view comments on posts, 
- schedule Post publication,
- send messages to other users.

### API Permissions:
- Only authenticated users can to perform actions such as creating posts, liking posts, and following/unfollowing users.
- Users should only to update and delete their own posts and comments.
- Users should only to update and delete their own profile.

## Getting Started

### Installing using GitHub

```shell
git clone https://github.com/TetyanaPavlyuk/social-media-api.git
cd social_media_api
```

### Run with Docker

Copy `.env.sample` to `.env`:
```shell
cp .env.sample .env
```
Populate the .env file with the required environment variables.

Build and run the containers
```shell
docker-compose build
docker-compose up
```

### Getting Access

Create superuser
```shell
docker-compose exec web python manage.py createsuperuser
```
Get access token via /api/user/token/

## Features

* JWT authenticated
* Admin panel /admin/
* Documentation is located at /api/doc/swagger-ui/
* Celery and Redis for schedule Post publication

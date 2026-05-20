# API Guide

## Authentication

Protected routes accept the saved session ID through the `X-Session-ID` header.
Swagger UI exposes this through the green **Authorize** button.

Session-creation routes:

- `POST /auth/login`
- `POST /auth/login/by/sessionid`
- `PATCH /auth/settings` accepts an optional saved session and returns a new
  session ID after settings are loaded.

Session-aware routes still accept legacy `sessionid` values from query
parameters, form data, or a `sessionid` cookie for backwards compatibility.

### Session Client Options

`POST /auth/login` and `POST /auth/login/by/sessionid` accept optional `proxy`,
`locale`, and `timezone` form fields. The service persists the proxy separately
from `aiograpi` settings because `Client.get_settings()` does not include proxy
transport state.

Use `PATCH /auth/settings` to update an existing session after login. Send the
session through `X-Session-ID` or the legacy `sessionid` form field, then pass
any of:

- `settings`: a JSON string from `aiograpi.Client.get_settings()`.
- `proxy`: proxy URL for all restored clients. Pass an empty value to clear it.
- `locale`: locale such as `en_US`.
- `timezone`: timezone offset in seconds, such as `10800`.

### Two-Factor Login

If `POST /auth/login` returns `TwoFactorRequired`, retry the same endpoint with
the same `username` and `password` plus `verification_code`.

If it returns `ChallengeRequired`, resolve the Instagram challenge in the
account/session context first, then retry login or import a known-good saved
session through `PATCH /auth/settings`.

If the challenge asks for an SMS or email code, call
`POST /auth/challenge/resolve` with the same `last_json` challenge payload and
the `security_code` from Instagram. The service injects that code into
`aiograpi` for one request and restores the default handler afterwards, so the
server never waits for stdin.

If Instagram says the username does not belong to an account, the API returns
HTTP 401 with a hint to check the username and retry `POST /auth/login`.

If Instagram returns `FeedbackRequired`, `PleaseWaitFewMinutes`, or
`RateLimitError`, the API returns HTTP 429. These errors usually mean Instagram
is throttling the account or action; pause automation, reduce request rate, and
check account and proxy health before retrying.

## Route Conventions

- `GET` routes read or download data.
- `POST` routes create sessions, create actions, or upload media.
- `PATCH` routes update state.
- `DELETE` routes remove or undo state.
- Paths use slash-separated resources such as `/story/upload/by/url`.
- State reversals use the same resource path with `DELETE`: for example,
  `POST /media/like` likes media and `DELETE /media/like` unlikes it.

## Relationship Actions

User relationship routes use `POST` to create or enable a relationship state and
`DELETE` to remove or disable it.

- `POST /user/follow` follows a user.
- `DELETE /user/follow` unfollows a user.
- `DELETE /user/follower` removes a follower.
- `POST /account/follow/request/approve` approves a pending follow request.
- `DELETE /account/follow/request` declines a pending follow request.
- `POST /account/follow/requests/approve` approves multiple pending follow requests.
- `DELETE /account/follow/requests` declines multiple pending follow requests.
- `POST /user/close-friend` adds a user to close friends.
- `DELETE /user/close-friend` removes a user from close friends.
- `POST /user/notifications/posts` enables post notifications for a user.
- `DELETE /user/notifications/posts` disables post notifications for a user.
- `POST /user/notifications/stories` enables story notifications for a user.
- `DELETE /user/notifications/stories` disables story notifications for a user.
- `POST /user/notifications/reels` enables Reel notifications for a user.
- `DELETE /user/notifications/reels` disables Reel notifications for a user.
- `POST /user/notifications/videos` enables video notifications for a user.
- `DELETE /user/notifications/videos` disables video notifications for a user.

## Account Settings

- `GET /account/security` returns security metadata for the authenticated
  account.
- `PATCH /account/biography` updates only the authenticated account biography.
- `PATCH /account/external-url` replaces the authenticated account external
  profile URL.
- `DELETE /account/external-url` clears the authenticated account external URL
  by asking Instagram to replace it with an empty URL. If Instagram rejects an
  empty URL for the account, remove the concrete bio link via
  `DELETE /account/bio-links`.
- `DELETE /account/bio-links` removes one or more bio links by `link_ids`.
- `PATCH /account/password` changes the authenticated account password.
- `POST /account/password/reset` sends a password reset flow for a username.
- `POST /account/email/confirm` sends an email confirmation code.
- `POST /account/phone/confirm` sends a phone confirmation code.

## Notification Settings

- `GET /notifications/settings` returns supported notification `content_type`
  values and allowed setting values.
- `PATCH /notifications/settings` updates one notification setting by
  `content_type` and `setting_value`. Most notification settings accept `off`,
  `following_only`, or `everyone`.
- `PATCH /notifications/settings` with `content_type=mute_all` accepts only
  `cancel`, `15_minutes`, `1_hour`, `2_hour`, `4_hour`, or `8_hour`.
- `DELETE /notifications/settings` disables all supported notification
  settings for the authenticated account.

## OpenAPI

- Swagger UI: `/docs`
- Raw schema: `/openapi.json`

The schema uses client-friendly operation IDs and request schema names so it can
be passed directly into OpenAPI client generators.

## Search

Search routes live under the `Search` tag and hide Instagram's internal
`fbsearch` naming behind resource-oriented paths:

- `GET /search/users` searches accounts by query.
- `GET /search/accounts` searches accounts through Instagram's newer search
  surface and supports `page_token`.
- `GET /search/followers` searches inside a user's followers.
- `GET /search/following` searches inside accounts a user follows.
- `GET /search/hashtags` searches hashtags.
- `GET /search/music` searches music tracks.
- `GET /search/locations` searches locations by name or coordinates.
- `GET /search/places` searches places by query with optional `lat` and `lng`
  ranking context.
- `GET /search/top` returns Instagram's blended top search results.
- `GET /search/top/flat` returns the older flat blended top-search list.
- `GET /search/web/top` returns web top-search results.
- `GET /search/web/hashtags` returns web hashtag search results.
- `GET /search/reels` returns Reel search results.
- `GET /search/item` returns one raw Instagram search tab by `item_id` and
  `search_surface`.
- `GET /search/suggested/users` returns suggested users for a profile.
- `GET /search/recent` returns the authenticated account's recent searches.
- `GET /search/typeahead` returns autocomplete suggestions for a partial query.
- `GET /search/typeahead/stream` returns the raw typeahead stream envelope.
- `GET /search/typeahead/users` returns flattened typeahead user suggestions.

`/search/top`, `/search/top/flat`, `/search/web/top`, `/search/reels`,
`/search/accounts`, `/search/typeahead`, `/search/typeahead/stream`, and
`/search/item` return raw Instagram-shaped objects because their payloads vary
by ranking surface and cursor state.

## Share

Share routes decode Instagram share URLs or encoded share codes without creating
or changing Instagram state.

- `GET /share?url=...` returns the decoded share `type`, `pk`, and extracted
  `code` for a share URL.
- `GET /share?code=...` returns the decoded share `type`, `pk`, and original
  `code` for an encoded share code.

## Highlight

Highlight routes manage Story highlights and accept either the Instagram
highlight PK or a highlight URL where lookup can be resolved from a URL:

- `GET /highlight?highlight_pk=...` returns highlight details by PK.
- `GET /highlight?url=...` resolves the PK from the URL and returns highlight
  details.
- `PATCH /highlight` updates title, cover, and story membership. A title-only
  patch uses aiograpi's dedicated title-change method, and `cover_picture`
  uploads a cover image through aiograpi's dedicated cover-change method.

## User Discovery

User discovery routes live under the target user context and return raw
Instagram-shaped objects where `aiograpi` exposes variable discovery payloads:

- `GET /user/suggestions` returns suggested users for a target profile.
- `GET /user/suggestions/details` returns expanded social context for
  suggestion IDs from `/user/suggestions`.
- `GET /user/recommendations` returns category-based recommended accounts for a
  target profile.
- `GET /user/creator` returns creator metadata for a target profile as
  `{ "user": ..., "info": ... }`.
- `GET /user/profile/web` returns Instagram's web-profile payload for a
  username.
- `GET /user/stream` returns a profile stream by `user_id` or `username`.
  `view=flat` returns the merged user payload; `view=raw` returns Instagram's
  stream envelope.
- `GET /user/friendships` returns relationship summaries for repeated
  `user_ids` query parameters.

`GET /account/feed/new` belongs to the authenticated account context and returns
whether Instagram says new timeline feed items are available.
`GET /account/feed/user/stream-item` returns a feed stream item for the
authenticated account.

## Reels

Global Reels feed routes live under the `Reels` tag and return arrays of media
objects. They accept `amount` and `last_media_pk` where the underlying
`aiograpi` method supports feed continuation.

- `GET /reels` returns connected Reels media.
- `GET /reels/friends` returns Friends tab Reels media.
- `GET /reels/explore` returns Explore Reels media.
- `GET /reels/timeline` returns Reels media for a `collection_pk`.

## Saved Collections

Saved collection routes live under the authenticated account context because
they read the current account's saved Instagram collections.

- `GET /account/collections` lists saved collections.
- `GET /account/collection` gets one saved collection by `collection_pk` or `name`.
- `GET /account/collection/media` lists media in one saved collection by
  `collection_pk` or `name`.

## Explore

Explore routes return raw Instagram-shaped objects because the Explore payload
depends on ranking, layout, and media type.

- `GET /explore` returns the authenticated account's Explore page.
- `GET /explore/media` returns Explore metadata for one `media_pk`.

## Tracks And Music

Track routes return Instagram music track data for Reels and post creation
workflows.

- `GET /track` gets a track by `id` or `canonical_id`.
- `GET /track/stream` returns streamed media for a track `id`.
- `GET /track/download/by/url` downloads track audio from a URL.
- `GET /music/feed/browser` returns music candidates for feed posts.

## Comment Utilities

Comment routes live under `Media (Post)` because Instagram comments always
belong to a media object.

- `GET /media/comments` lists a paginated comment page with `next_cursor`.
- `GET /media/comments/stream` lists a stream comment page with `min_cursor`
  and `max_cursor`.
- `POST /media/comment` creates a comment or reply.
- `DELETE /media/comment` deletes one comment from media.
- `GET /media/comment/replies` lists replies for one comment.
- `POST /media/comment/like` likes a comment.
- `DELETE /media/comment/like` unlikes a comment.
- `GET /media/comment/likers` lists users who liked a comment.
- `POST /media/comment/pin` pins a comment.
- `DELETE /media/comment/pin` unpins a comment.
- `GET /media/comment/infos` returns comment counters for media IDs.
- `POST /media/comment/check/offensive` checks whether text is offensive for
  the target media.

## Direct

- `GET /direct/pending/inbox` lists pending direct request threads up to
  `amount`.
- `GET /direct/spam/inbox` lists spam direct request threads up to `amount`.
- `POST /direct/request/approve` approves a direct message request thread.
- `POST /direct/thread/message` replies in an existing direct thread.
- `DELETE /direct/message` unsends a direct message.
- `POST /direct/cutout/sticker` sends a cutout sticker to either `user_ids`
  or `thread_ids`.

## Pagination

Paginated read-list routes return an object with `items` and `next_cursor`.
Pass the returned `next_cursor` as `cursor` on the next request to continue
from the previous page. This shape is used for:

- `GET /direct/inbox`
- `GET /direct/pending`
- `GET /direct/spam`
- `GET /hashtag/media/recent`
- `GET /hashtag/media/top`
- `GET /location/media/recent`
- `GET /location/media/top`
- `GET /media/comments`
- `GET /media/comments/stream` returns `items`, `min_cursor`, and `max_cursor`
  instead of `next_cursor`.
- `GET /story/archive`
- `GET /story/viewers`
- `GET /user/reels`
- `GET /account/follow/requests`
- `GET /user/followers`
- `GET /user/following`
- `GET /user/posts`
- `GET /user/tagged/posts`
- `GET /user/videos`

User post collection routes accept either `user_id` for numeric Instagram
user PKs or `username` for usernames. If a legacy client passes a username in
`user_id`, the service resolves it before calling `aiograpi`.

Additional discovery collection routes return plain arrays when `aiograpi` does
not expose a cursor for the underlying method:

- `GET /hashtag/related`
- `GET /hashtag/reels`
- `GET /location/guides`
- `GET /user/guides`
- `GET /user/pinned/posts`

## Form JSON Fields

Story upload decoration fields such as `mentions`, `locations`, `links`,
`hashtags`, and `stickers` are form fields. Repeat the field with one
JSON-encoded object per value, or pass a single JSON array of objects.
For mentions, locations, and hashtags, omitted `x`, `y`, `width`, `height`, or
`rotation` values default to a centered story position before the request is
sent to `aiograpi`.

Feed upload and edit metadata use JSON-encoded form strings too. The upload
endpoints for photo, video, clip/Reels, IGTV, album/carousel, and the media
edit endpoint accept `usertags` as one JSON array or repeated JSON-encoded
`Usertag` values, and `location` as one JSON-encoded `Location` object. Leave
these fields empty or omit them when no metadata is needed.

## System Endpoints

- `GET /health` returns `{"status":"ok"}` for liveness.
- `GET /ready` checks storage and required runtime dependencies.
- `GET /metrics` exports Prometheus text metrics.
- `GET /build` returns service build metadata.
- `GET /deps` returns runtime dependency versions.

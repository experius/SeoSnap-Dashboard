# Seosnap Dashboard
## Usage
* Create a website in the admin panel
* Add a sitemap, url and cacheable field to the website
* Save the website id and use it with [cachewarmer](https://github.com/experius/SeoSnap-Cache-Warmer)
* View the cached pages and their metadata

### Setup crawl error reporting
* Modify .env file fields: `EMAIL_HOST`, `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
* Set per site error reporting treshold and timeout


## Development
TO run the dashboard run the following
```
# Install
make install

# Serve
make serve
## For development use
make serve_dev
```

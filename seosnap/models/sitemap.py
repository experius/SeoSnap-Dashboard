import requests, xmltodict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import copy

class Sitemap:

    def __init__(self, w):
        self.website = w

    def get_data(self):
        r = requests.get(self.website.sitemap)
        rootDict = xmltodict.parse(r.text, force_list={'url'})

        urls = []
        mobile_urls = []
        if "urlset" in rootDict:
            urls = rootDict['urlset']['url']

            for i, d in enumerate(urls):
                urls[i] = self._change_page_data(d, False)

            # when using enumerate you can't append this will cause an infinity loop
            for d in urls:
                mobile_urls.append(self._change_page_data(copy(d), True))

        if "sitemapindex" in rootDict:
            threads = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                for sitemap in rootDict['sitemapindex']['sitemap']:
                    threads.append(executor.submit(self._get_sitemap_data, sitemap['loc']))

                for task in as_completed(threads):
                    result = task.result()
                    urls.extend(result)

        urls.extend(mobile_urls)

        return urls

    def _get_sitemap_data(self, sitemapUrl):
        r = requests.get(sitemapUrl)
        rootDict = xmltodict.parse(r.text, force_list={'url'})
        data = rootDict['urlset']['url']
        mobile_data = []

        for i, d in enumerate(data):
            data[i] = self._change_page_data(d, False)

        # when using enumerate you can't append this will cause an infinity loop
        for d in data:
            mobile_data.append(self._change_page_data(copy(d), True))

        data.extend(mobile_data)

        return data

    def _change_page_data(self, page, is_mobile):
        url = page['loc']
        if url.startswith(self.website.domain):
            url = "/" + url[len(self.website.domain):]
        if is_mobile:
            url = url + "?mobile=1"

        page['loc'] = url

        if "lastmod" in page and page['lastmod'] is not None and not is_mobile:
            page['lastmod'] = datetime.strptime(page['lastmod'], '%Y-%m-%dT%H:%M:%S%z')
        else:
            page['lastmod'] = None

        return page

from django.urls import path

from seosnap import views

website_list = views.WebsiteViewSet.as_view({'get': 'list'})
website_detail = views.WebsiteViewSet.as_view({'get': 'retrieve'})
website_reporting_failure = views.WebsiteReportFailure.as_view({'post': 'report_failure'})

website_report = views.WebsiteReport.as_view({'get': 'get_logging'})

website_pages = views.PageWebsiteList.as_view({'get': 'pages'})
website_pages_count = views.PageWebsiteList.as_view({'get': 'count'})
website_pages_sync = views.PageWebsiteList.as_view({'get': 'sync'})
website_pages_update = views.PageWebsiteUpdate.as_view({'put': 'update_pages'})
website_pages_clean = views.PageWebsiteClean.as_view({'delete': 'clean_pages'})

website_queue = views.QueueWebsiteList.as_view({'get': 'queue'})
website_queue_progression = views.QueueWebsiteList.as_view({'get': 'queue_progress'})
website_queue_todo_count = views.QueueWebsiteList.as_view({'get': 'todo_count'})
website_queue_redo_old = views.QueueWebsiteList.as_view({'post': 'redo_old'})
website_queue_update = views.QueueWebsiteUpdate.as_view({'put': 'update_queue'})
website_queue_priority_update = views.QueueWebsiteUpdate.as_view({'put': 'update_priority'})
website_queue_items_priority_update = views.QueueWebsiteUpdate.as_view({'post': 'items_update_priority'})

website_queue_clean = views.QueueWebsiteClean.as_view({'delete': 'clean_queue'})
website_queue_delete_item = views.QueueWebsiteClean.as_view({'delete': 'delete_queue_item'})
website_queue_delete_multiple_items = views.QueueWebsiteClean.as_view({'post': 'delete_multiple_queue_items'})

website_cache_redo_tags = views.RedoPageCache.as_view({'post': 'cache_redo_tag'})
website_cache_redo_website = views.RedoPageCache.as_view({'post': 'cache_redo_website'})
multiple_website_cache_redo_website = views.RedoPageCache.as_view({'post': 'multiple_cache_redo_website'})
website_cache_redo_pages = views.RedoPageCache.as_view({'post': 'cache_redo_addresses'})

# URLs for multiple sites
pages = views.Pages.as_view({'get': 'get_pages'})
queues = views.Queues.as_view({'get': 'get_queues'})
cache_redo_tags = views.Pages.as_view({'post': 'cache_redo_tag'})

urlpatterns = [
    path('websites', website_list, name='websites-list'),
    path('websites/<int:pk>', website_detail, name='websites-retrieve'),
    path('websites/<int:website_id>/reporting', website_reporting_failure, name='websites-reporting'),

    path('websites/log', website_report, name='websites-report-loging'),

    path('websites/<int:website_id>/pages', website_pages, name='websites-pages-list'),
    path('websites/<int:website_id>/pages/count', website_pages_count, name='websites-pages-count'),
    path('websites/<int:website_id>/pages/sync', website_pages_sync, name='websites-pages-sync'),

    path('websites/<int:website_id>/pages/update', website_pages_update, name='websites-pages-update'),
    path('websites/<int:website_id>/pages/clean', website_pages_clean, name='websites-pages-clean'),
    path('websites/<int:website_id>/queue', website_queue, name='websites-queue-list'),

    path('websites/<int:website_id>/queue/progression', website_queue_progression, name='websites-queue-list-progression'),
    path('websites/<int:website_id>/queue/todo/count', website_queue_todo_count, name='websites-queue-todo-count'),
    path('websites/<int:website_id>/queue/redo/old', website_queue_redo_old, name='websites-queue-redo-old'),
    path('queue/<int:queue_item_id>/priority', website_queue_priority_update, name='websites-queue-priority-update'),
    path('queue/items/priority', website_queue_items_priority_update, name='websites-queue-items-priority-update'),

    path('websites/<int:website_id>/queue/update', website_queue_update, name='websites-queue-update'),

    path('websites/<int:website_id>/queue/clean', website_queue_clean, name='websites-queue-clean'),
    path('queue/<int:queue_item_id>/delete', website_queue_delete_item, name='websites-queue-delete-item'),
    path('queue/items/delete', website_queue_delete_multiple_items, name='websites-multiple-queue-delete-items'),

    path('websites/<int:website_id>/cache/redo/tags', website_cache_redo_tags, name='websites-cache-redo-tags'),
    path('cache/redo/website', website_cache_redo_website, name='websites-cache-redo-website'),
    path('multiple/cache/redo/website', multiple_website_cache_redo_website, name='multiple-websites-cache-redo-website'),
    path('websites/<int:website_id>/pages/redo', website_cache_redo_pages, name='websites-cache-redo-addresses'),

    # TODO Multiple get
    path('pages', pages, name='pages-list'),
    path('queues', queues, name='queues-list'),
    path('cache/redo/tags', cache_redo_tags, name='websites-pages-list'),

]

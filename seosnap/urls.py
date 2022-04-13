from django.urls import path

from seosnap import views

website_list = views.WebsiteViewSet.as_view({'get': 'list'})
website_detail = views.WebsiteViewSet.as_view({'get': 'retrieve'})
website_reporting = views.WebsiteReportFailure.as_view({'post': 'report_failure'})

website_pages = views.PageWebsiteList.as_view({'get': 'pages'})
website_pages_count = views.PageWebsiteList.as_view({'get': 'count'})
website_pages_sync_pages = views.PageWebsiteList.as_view({'get': 'sync_pages'})
website_pages_update = views.PageWebsiteUpdate.as_view({'put': 'update_pages'})
website_pages_clean = views.PageWebsiteClean.as_view({'delete': 'clean_pages'})

website_queue = views.QueueWebsiteList.as_view({'get': 'queue'})
website_queue_progression = views.QueueWebsiteList.as_view({'get': 'queueProgress'})
website_queue_todo_count = views.QueueWebsiteList.as_view({'get': 'todoCount'})
website_queue_update = views.QueueWebsiteUpdate.as_view({'put': 'update_queue'})
website_queue_clean = views.QueueWebsiteClean.as_view({'delete': 'clean_queue'})

website_cache_redo_tags = views.RedoPageCache.as_view({'post': 'cache_redo_tag'})
website_cache_redo_website = views.RedoPageCache.as_view({'post': 'cache_redo_website'})

urlpatterns = [
    path('websites', website_list, name='websites-list'),
    path('websites/<int:pk>', website_detail, name='websites-retrieve'),
    path('websites/<int:website_id>/reporting', website_reporting, name='websites-reporting'),
    path('websites/<int:website_id>/pages', website_pages, name='websites-pages-list'),
    path('websites/<int:website_id>/pages/count', website_pages_count, name='websites-pages-count'),
    path('websites/<int:website_id>/pages/sync', website_pages_sync_pages, name='websites-pages-sync_pages'),

    path('websites/<int:website_id>/pages/update', website_pages_update, name='websites-pages-update'),
    path('websites/<int:website_id>/pages/clean', website_pages_clean, name='websites-pages-clean'),
    path('websites/<int:website_id>/queue', website_queue, name='websites-queue-list'),

    path('websites/<int:website_id>/queue/progression', website_queue_progression, name='websites-queue-list-progression'),
    path('websites/<int:website_id>/queue/todo/count', website_queue_todo_count, name='websites-queue-todo-count'),

    path('websites/<int:website_id>/queue/update', website_queue_update, name='websites-queue-update'),
    path('websites/<int:website_id>/queue/clean', website_queue_clean, name='websites-queue-clean'),

    path('websites/<int:website_id>/cache/redo/tags', website_cache_redo_tags, name='websites-cache-redo-tags'),
    path('websites/<int:website_id>/cache/redo/website', website_cache_redo_website, name='websites-cache-redo-website'),
]

from django.urls import path

from seosnap import views

website_list = views.WebsiteViewSet.as_view({'get': 'list'})
website_detail = views.WebsiteViewSet.as_view({'get': 'retrieve'})
website_reporting = views.WebsiteReportFailure.as_view({'post': 'report_failure'})

website_pages = views.PageWebsiteList.as_view({'get': 'pages'})
website_pages_update = views.PageWebsiteUpdate.as_view({'put': 'update_pages'})
website_pages_clean = views.PageWebsiteClean.as_view({'delete': 'clean_pages'})

website_queue = views.QueueWebsiteList.as_view({'get': 'queue'})
website_queue_update = views.QueueWebsiteUpdate.as_view({'put': 'update_queue'})
website_queue_clean = views.QueueWebsiteClean.as_view({'delete': 'clean_queue'})

urlpatterns = [
    path('websites', website_list, name='websites-list'),
    path('websites/<int:pk>', website_detail, name='websites-retrieve'),
    path('websites/<int:website_id>/reporting', website_reporting, name='websites-reporting'),
    path('websites/<int:website_id>/pages', website_pages, name='websites-pages-list'),
    path('websites/<int:website_id>/pages/update', website_pages_update, name='websites-pages-update'),
    path('websites/<int:website_id>/pages/clean', website_pages_clean, name='websites-pages-clean'),
    path('websites/<int:website_id>/queue', website_queue, name='websites-queue-list'),
    path('websites/<int:website_id>/queue/update', website_queue_update, name='websites-queue-update'),
    path('websites/<int:website_id>/queue/clean', website_queue_clean, name='websites-queue-clean'),
]

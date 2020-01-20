from django.urls import include, path

from seosnap import views

website_list = views.WebsiteViewSet.as_view({'get': 'list'})
website_detail = views.WebsiteViewSet.as_view({'get': 'retrieve'})
website_pages = views.PageWebsiteList.as_view({'get': 'pages'})
website_pages_update = views.PageWebsiteUpdate.as_view({'put': 'update_pages'})

urlpatterns = [
    path('websites', website_list, name='websites-list'),
    path('websites/<int:pk>', website_detail, name='websites-retrieve'),
    path('websites/<int:website_id>/pages', website_pages, name='websites-pages-list'),
    path('websites/<int:website_id>/pages/update', website_pages_update, name='websites-pages-update'),
]

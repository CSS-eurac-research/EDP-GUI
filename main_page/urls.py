from django.urls import path
from . import views
from main_page.admin import admin
from django.contrib import admin


app_name = 'edp_portal'
urlpatterns = [
    path('', views.main_page, name='main_page'),
    #path('admin/', admin.site.urls),
    path('docs/', views.DocsPageView.as_view(), name='docs_page'),
    path('jupyter/', views.jupyter_page, name='jupyter_page'),
    path('openeo/', views.openeo_page, name='openeo_page'),
    path('pgadmin/', views.pgadmin_page, name='pgadmin_page'),
    path('maps/', views.maps_page, name='maps_page'),
    path('terms-and-conditions/', views.terms_conditions_page, name='terms_conditions_page'),
    path('discovery/', views.discovery, name='discovery'),
    path('discovery/<slug:uuid>', views.result_detail, name='result_detail'),
    path('discovery/linkset/<slug:uuid>', views.get_linkset, name='get_linkset'),
]
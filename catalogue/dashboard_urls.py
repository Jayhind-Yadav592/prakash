from django.urls import path
from . import dashboard_views

app_name = 'dashboard'

urlpatterns = [
    # Authentication
    path('login/', dashboard_views.dashboard_login, name='login'),
    path('logout/', dashboard_views.dashboard_logout, name='logout'),

    # Dashboard Overview
    path('', dashboard_views.dashboard_home, name='home'),

    # Medicines
    path('medicines/', dashboard_views.dashboard_medicine_list, name='medicine_list'),
    path('medicines/add/', dashboard_views.dashboard_medicine_add, name='medicine_add'),
    path('medicines/edit/<int:pk>/', dashboard_views.dashboard_medicine_edit, name='medicine_edit'),
    path('medicines/delete/<int:pk>/', dashboard_views.dashboard_medicine_delete, name='medicine_delete'),

    # Categories
    path('categories/', dashboard_views.dashboard_category_list, name='category_list'),
    path('categories/add/', dashboard_views.dashboard_category_add, name='category_add'),
    path('categories/edit/<int:pk>/', dashboard_views.dashboard_category_edit, name='category_edit'),
    path('categories/delete/<int:pk>/', dashboard_views.dashboard_category_delete, name='category_delete'),
]

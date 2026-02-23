from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('add/', views.item_add, name='item_add'),
    path('edit/<int:pk>/', views.item_edit, name='item_edit'),
    path('delete/<int:pk>/', views.item_delete, name='item_delete'),
    path('print/', views.print_barcodes, name='print_barcodes'),

    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),
    path('users/barcode/regen/<int:pk>/', views.regenerate_user_barcode, name='regenerate_user_barcode'),

    # Borrowing
    path('borrow/', views.borrow_item, name='borrow_item'),

    # Returns
    path('borrowed/', views.borrowed_items_list, name='borrowed_items_list'),
    path('borrowed/return/<int:pk>/', views.return_item, name='return_item'),
    path('borrowed/history/', views.borrowing_history_list, name='borrowing_history_list'),
    path('borrowed/history/export/', views.export_borrowing_history, name='export_borrowing_history'),
    path('borrowed/history/clear/', views.clear_returned_history, name='clear_returned_history'),
    path('my_borrowed_items/', views.user_borrowed_items, name='user_borrowed_items'),
    path('items/suggestions/', views.item_search_suggestions, name='item_search_suggestions'),

    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Groups
    path('add-group/', views.add_group, name='add_group'),
    path('lesson/<int:group_id>/<str:lesson_date>/', views.lesson_detail, name='lesson_detail'),

    # Students
    path('students/', views.students, name='students'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),

    # Purchases
    path('students/<int:student_id>/add-purchase/', views.add_purchase, name='add_purchase'),
    path('purchases/<int:purchase_id>/mark-paid/', views.mark_purchase_paid, name='mark_purchase_paid'),
]
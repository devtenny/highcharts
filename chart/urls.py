from django.urls import path
from chart import views  # !!!

urlpatterns = [
    path('', views.home, name='home'),
    path('ticket-class/1/',
         views.ticket_class_view_1, name='ticket_class_view_1'),
    path('ticket-class/2/',
         views.ticket_class_view_2, name='ticket_class_view_2'),
    path('ticket-class/3/',
         views.ticket_class_view_3, name='ticket_class_view_3'),
    path('world-population/',
         views.world_population, name='world_population'),  # !!!
    path('json-example/', views.json_example, name='json_example'),
    path('json-example/data/', views.chart_data, name='chart_data'),
    path('covid19/jupyterlab/', views.covid19_chart_jupyterlab, name='covid19_chart_jupyterlab'),
    path('covid19/confirmed/', views.covid19_chart_confirmed, name='covid19_chart_confirmed'),
    path('covid19/recovered/', views.covid19_chart_recovered, name='covid19_chart_recovered'),
    path('covid19/deaths/', views.covid19_chart_deaths, name='covid19_chart_deaths'),
    path('ticket-class/final/',
         views.ticket_class_view_final, name='ticket_class_view_final'),
]

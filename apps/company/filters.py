from django.db.models import Q
import django_filters
from apps.company.models import CompanyProfile


class CompanyProfileFilter(django_filters.FilterSet):
    company_name = django_filters.CharFilter(method='filter_name')

    class Meta:
        model = CompanyProfile
        fields = ['company_name']

    def filter_name(self, queryset, name, value):
        if value:
            return queryset.filter(Q(company_name__icontains=value))
        return queryset

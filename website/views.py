from website.utils import get_website_title
from django.views.generic.detail import DetailView
from website.models import Application
from django.views.generic.base import TemplateView
from django.views.generic import ListView, CreateView
from django.utils import timezone


class ApplicationView(CreateView):
    model = Application
    fields = ["input"]

    def form_valid(self, form):
        form.instance.user = self.request.user
        print(form.instance.id)
        form.instance.reference_id = form.instance.id
        return super(ApplicationView, self).form_valid(form)


class ApplicationDetailView(DetailView):
    model = Application

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        context["title"] = get_website_title(self.get_object().input)
        return context


class Dashboard(ListView):
    pass


class Index(TemplateView):
    template_name = "index.html"

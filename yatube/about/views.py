from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Об авторе'
        context['text'] = (
            'Меня зовут Игорь. Я студент 5 курса '
            '<a href=https://mai.ru/education/studies/institutes/space/>'
            'Московского Авиационного Института. '
            'Институт №6 "Аэрокосмический".</a>'
        )
        return context


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Об авторе'
        context['text'] = (
            'Какие-то технологии были и я их предерживался:)'
        )
        return context

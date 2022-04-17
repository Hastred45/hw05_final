from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Contact

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class ContactForm(forms.ModelForm):
    class Meta:
        # На основе какой модели создаётся класс формы
        model = Contact
        # Укажем, какие поля будут в форме
        fields = ('name', 'email', 'subject', 'body')

        # Метод-валидатор для поля subject
    def clean_subject(self):
        data = self.cleaned_data['subject']
        # Если пользователь не поблагодарил - считаем это ошибкой
        if 'спасибо' not in data.lower():
            raise forms.ValidationError(
                'Вы обязательно должны нас поблагодарить!'
            )

        # Метод-валидатор обязательно должен вернуть очищенные данные,
        # даже если не изменил их
        return data

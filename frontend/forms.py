import random
from django import forms

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    username  = forms.CharField(max_length=150)
    email     = forms.EmailField(required=False)
    password  = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password2"):
            self.add_error("password2", "Passwords must match.")
        return cleaned

class TopicForm(forms.Form):
    topic = forms.CharField(label="Quiz topic")

    # Dynamic placeholder examples
    PLACEHOLDERS = [
        "All US presidents from Massachusetts",
        "2015 Hawks starting lineup",
        "Countries that begin with M",
        "Top 10 Oscar Best Picture winners",
        "Famous classical composers",
        "Biggest tech companies by market cap"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ph = random.choice(self.PLACEHOLDERS)
        self.fields['topic'].widget = forms.TextInput(
            attrs={
                "placeholder": ph,
                "style": "padding:0.5em; width:100%; box-sizing:border-box;"
            }
        )


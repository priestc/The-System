from django import forms
from models import S3Bucket

class S3BucketForm(forms.ModelForm):
    class Meta:
        model = S3Bucket
    

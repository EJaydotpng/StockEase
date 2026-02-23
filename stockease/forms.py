from django import forms
from .models import Borrowing
from django.contrib.auth.models import User
from .models import Item, Profile

class BorrowForm(forms.Form):
    item_barcode = forms.CharField(max_length=20, label="Item Barcode")
    user_identifier = forms.CharField(max_length=20, label="User Barcode or Username")
    quantity = forms.IntegerField(min_value=1, label="Quantity to Borrow")

    def clean(self):
        cleaned_data = super().clean()
        user_identifier = cleaned_data.get('user_identifier')
        item_barcode = cleaned_data.get('item_barcode')
        quantity = cleaned_data.get('quantity')

        self.user = None
        self.item = None

        if user_identifier:
            # Try to find user by barcode
            try:
                profile = Profile.objects.get(barcode=user_identifier)
                self.user = profile.user
            except Profile.DoesNotExist:
                # If not found by barcode, try by username
                try:
                    self.user = User.objects.get(username=user_identifier)
                except User.DoesNotExist:
                    self.add_error('user_identifier', 'User not found by barcode or username.')
        
        if item_barcode:
            try:
                self.item = Item.objects.get(barcode=item_barcode)
            except Item.DoesNotExist:
                self.add_error('item_barcode', 'Item not found.')
        
        if self.item and quantity:
            if self.item.quantity < quantity:
                self.add_error('quantity', f'Only {self.item.quantity} of {self.item.name} available.')

        return cleaned_data


class ReturnForm(forms.Form):
    returned_quantity = forms.IntegerField(min_value=1, label="Quantity to Return")

    def __init__(self, *args, **kwargs):
        self.borrowing_record = kwargs.pop('borrowing_record', None)
        super().__init__(*args, **kwargs)
        if self.borrowing_record:
            self.fields['returned_quantity'].max_value = self.borrowing_record.quantity
            self.fields['returned_quantity'].help_text = f"Max quantity to return: {self.borrowing_record.quantity}"
    
    def clean_returned_quantity(self):
        returned_quantity = self.cleaned_data['returned_quantity']
        if self.borrowing_record and returned_quantity > self.borrowing_record.quantity:
            raise forms.ValidationError(f"Cannot return more than borrowed ({self.borrowing_record.quantity}).")
        return returned_quantity

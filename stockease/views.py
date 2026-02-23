from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q # Import Q for complex queries
from django.http import JsonResponse, HttpResponse
import csv
from datetime import datetime
from .models import Item, Profile, Borrowing
from django import forms
from .forms import BorrowForm, ReturnForm # Import the new forms

# --- User Management Forms and Views ---

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff', 'is_active']

@staff_member_required
def user_list(request):
    all_users = User.objects.all().select_related('profile').order_by('username')
    superusers = all_users.filter(is_superuser=True)
    regular_users = all_users.filter(is_superuser=False)
    return render(request, 'stockease/user_list.html', {
        'superusers': superusers,
        'regular_users': regular_users
    })

@staff_member_required
def user_edit(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user_to_edit)
    return render(request, 'stockease/user_form.html', {'form': form, 'user_to_edit': user_to_edit})

@staff_member_required
def user_delete(request, pk):
    user_to_delete = get_object_or_404(User, pk=pk)
    # Prevent admin from deleting themselves
    if request.user.pk == user_to_delete.pk:
        return redirect('user_list')
    if request.method == 'POST':
        user_to_delete.delete()
        return redirect('user_list')
    return render(request, 'stockease/user_confirm_delete.html', {'user_to_delete': user_to_delete})

@staff_member_required
def regenerate_user_barcode(request, pk):
    user = get_object_or_404(User, pk=pk)
    # Ensures a profile exists, creating one if it's missing for any reason.
    profile, created = Profile.objects.get_or_create(user=user)
    profile.barcode = '' # Clear the barcode
    profile.save()      # Re-save to trigger generation of a new one
    return redirect('user_edit', pk=user.pk)

# --- End User Management ---


# Form for Item
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'quantity', 'image']

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def item_list(request):
    items = Item.objects.all()
    query = request.GET.get('q')
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'stockease/item_list.html', {'items': items, 'query': query})

@staff_member_required
def item_add(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('item_list')
    else:
        form = ItemForm()
    return render(request, 'stockease/item_form.html', {'form': form, 'title': 'Add Item'})

@staff_member_required
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('item_list')
    else:
        form = ItemForm(instance=item)
    return render(request, 'stockease/item_form.html', {'form': form, 'title': 'Edit Item'})

@staff_member_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('item_list')
    return render(request, 'stockease/item_confirm_delete.html', {'item': item})

@staff_member_required
def print_barcodes(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_items')
        if not selected_ids:
            # Handle case where form is submitted with no items selected
            items = Item.objects.none() # Or redirect with a message
            title = "No Items Selected"
        else:
            items = Item.objects.filter(id__in=selected_ids)
            title = "Printing Selected Item Barcodes"
    else:
        items = Item.objects.all()
        title = "Printing All Item Barcodes"
    
    context = {
        'items': items,
        'title': title
    }
    return render(request, 'stockease/print_barcodes.html', context)


@staff_member_required
def borrow_item(request):
    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            user = form.user # User object retrieved in form's clean method
            item = form.item # Item object retrieved in form's clean method
            quantity = form.cleaned_data['quantity']

            # Create borrowing record
            Borrowing.objects.create(user=user, item=item, initial_quantity=quantity, quantity=quantity)

            # Update item quantity
            item.quantity -= quantity
            item.save()

            messages.success(request, f'{quantity} x {item.name} borrowed by {user.username}.')
            return redirect('borrow_item') # Redirect to clear form
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_data = {}
        item_barcode_from_url = request.GET.get('item_barcode')
        if item_barcode_from_url:
            initial_data['item_barcode'] = item_barcode_from_url
        form = BorrowForm(initial=initial_data)
    
    return render(request, 'stockease/borrow_item.html', {'form': form, 'title': 'Borrow Item'})


@staff_member_required
def borrowed_items_list(request):
    borrowings = Borrowing.objects.filter(return_date__isnull=True).order_by('-borrow_date')
    return render(request, 'stockease/borrowed_items_list.html', {'borrowings': borrowings})


@staff_member_required
def borrowing_history_list(request):
    history = Borrowing.objects.all().order_by('-borrow_date')
    return render(request, 'stockease/borrowing_history_list.html', {'history': history})


@staff_member_required
def export_borrowing_history(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="borrowing_history_{}.csv"'.format(datetime.now().strftime("%Y%m%d-%H%M%S"))

    writer = csv.writer(response)
    writer.writerow(['User', 'User Barcode', 'Item', 'Item Barcode', 'Initial Quantity', 'Borrowed On', 'Returned On', 'Status'])

    history = Borrowing.objects.all().order_by('-borrow_date')
    for record in history:
        status = "Returned" if record.return_date else "Active"
        writer.writerow([
            record.user.username,
            record.user.profile.barcode,
            record.item.name,
            record.item.barcode,
            record.initial_quantity,
            record.borrow_date.strftime("%Y-%m-%d %H:%M:%S"),
            record.return_date.strftime("%Y-%m-%d %H:%M:%S") if record.return_date else '',
            status
        ])
    return response


@staff_member_required
def clear_returned_history(request):
    returned_count = Borrowing.objects.filter(return_date__isnull=False).count()
    if request.method == 'POST':
        # Delete all records that have a return date (completed loans)
        Borrowing.objects.filter(return_date__isnull=False).delete()
        messages.success(request, f'Successfully cleared {returned_count} returned records from the history logs.')
        return redirect('borrowing_history_list')
    
    return render(request, 'stockease/clear_history_confirm.html', {'count': returned_count})


def item_search_suggestions(request):
    query = request.GET.get('term', '')
    if query:
        items = Item.objects.filter(Q(name__icontains=query) | Q(description__icontains=query)).values_list('name', flat=True)[:10]
    else:
        items = []
    return JsonResponse(list(items), safe=False)


@login_required
def user_borrowed_items(request):
    # Filter for items borrowed by the current user and not yet returned
    borrowings = Borrowing.objects.filter(
        user=request.user,
        return_date__isnull=True
    ).order_by('-borrow_date')
    return render(request, 'stockease/user_borrowed_items.html', {'borrowings': borrowings})


@staff_member_required
def return_item(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk, return_date__isnull=True)
    item = borrowing.item
    
    if request.method == 'POST':
        form = ReturnForm(request.POST, borrowing_record=borrowing)
        if form.is_valid():
            returned_quantity = form.cleaned_data['returned_quantity']

            # Update item quantity in inventory
            item.quantity += returned_quantity
            item.save()

            # Update borrowing record
            borrowing.quantity -= returned_quantity
            if borrowing.quantity == 0:
                borrowing.return_date = timezone.now()
                messages.success(request, f'{returned_quantity} x {item.name} fully returned by {borrowing.user.username}. Loan closed.')
            else:
                messages.success(request, f'{returned_quantity} x {item.name} partially returned by {borrowing.user.username}. {borrowing.quantity} remaining.')
            borrowing.save()
            return redirect('borrowed_items_list')

        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReturnForm(initial={'returned_quantity': borrowing.quantity}, borrowing_record=borrowing)

    context = {
        'form': form,
        'borrowing': borrowing,
        'title': f'Return {borrowing.item.name}'
    }
    return render(request, 'stockease/return_item.html', context)

from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
import random
from django.contrib.auth import authenticate,login,logout
from .models import RealEstateUser, PropertyCategory, Property, CustomerInquiry, PropertyImage
from django.db.models import Q
from django.db.models import Sum

# Report and Statistics

from django.http import HttpResponse
from django.db.models import Count
from django.utils import timezone

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.chart import PieChart, BarChart, Reference

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle



# Download Property Details

import os
import zipfile
from io import BytesIO
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

from .models import Property, PropertyImage


# Create your views here.
def base(request):
    return render(request, 'public/base.html')

def index(request):
    featured_properties = Property.objects.filter(featured_property=True,status='Available').prefetch_related('images')
    return render(request, 'public/index.html', {'featured_properties': featured_properties,})

def about(request):
    return render(request, 'public/about.html')

def agents(request):
    return render(request, 'public/agents.html')

def contact(request):
    if request.method=='POST':
        last_inquiry = CustomerInquiry.objects.order_by('-id').first()
        if last_inquiry:
            next_id = last_inquiry.id + 1
        else:
            next_id = 1
        inquiry_code = str(next_id).zfill(5)
        full_name=request.POST['full_name']
        email=request.POST['email']
        subject=request.POST['subject']
        message=request.POST['message']

        CustomerInquiry.objects.create(inquiry_code=inquiry_code,full_name=full_name,email=email, subject=subject, message=message)
        messages.success(request, "✅ Send inquiry successful! We will get back to you shortly.")
    return render(request, 'public/contact.html')


def careers(request):
    return render(request, 'public/careers.html')


# def properties(request):
#     featured_properties = Property.objects.filter(featured_property=True,status='Available').prefetch_related('images')
#     return render(request, 'public/properties.html', {'featured_properties': featured_properties})

def properties(request):
    featured_properties = Property.objects.filter(
        featured_property=True,
        status='Available'
    ).prefetch_related('images')

    all_properties = Property.objects.filter(
        status='Available'
    ).prefetch_related('images')

    return render(request, 'public/properties.html', {
        'featured_properties': featured_properties,
        'all_properties': all_properties,
    })



def property_details(request, id):
    property = get_object_or_404(Property, id=id)
    return render(request, 'public/property_details.html', {'property': property})

def send_property_inquiry(request, id):
    property = get_object_or_404(Property, id=id)

    if request.method == 'POST':
        last_inquiry = CustomerInquiry.objects.order_by('-id').first()
        next_id = (last_inquiry.id + 1) if last_inquiry else 1
        inquiry_code = str(next_id).zfill(5)

        full_name = request.POST['full_name']
        email = request.POST['email']
        subject = f"{property.property_code} - {property.title}"
        status='Assigned'
        message = request.POST['message']

        assigned_to = property.agent if property.agent else None

        CustomerInquiry.objects.create(
            inquiry_code=inquiry_code,
            full_name=full_name,
            email=email,
            subject=subject,
            assigned_to=assigned_to,
            status=status,
            message=message
        )

        messages.success(request, "✅ Inquiry sent successfully! We will get back to you shortly.")
        return redirect('send_property_inquiry', id=id)

    return render(request, 'public/send_property_inquiry.html', {'property': property})


def services(request):
    return render(request, 'public/services.html')

def login_view(request):
    if request.method =="POST":
        username = request.POST['username']
        password=request.POST['password']
        user = authenticate(request, username=username, password=password)
        print("Test it in here :",user)
        if user is not None:
            login(request,user)
            if user.role=="Admin":
                return redirect('admin_dashboard')
            elif user.role=="Agent":
                return redirect('agent_dashboard')
        messages.error(request, "❌ Invalid username and password. Please try again.")
        return redirect("login")
    return render(request, 'public/login.html')


@login_required
def admin_dashboard(request):
    return render(request, 'admin/admin_dashboard.html')

@login_required
def admin_base(request):
    return render(request, 'admin/admin_base.html')

@login_required
def agent_dashboard(request):
    return render(request, 'agent/agent_dashboard.html')

@login_required
def agent_base(request):
    return render(request, 'agent/agent_base.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('index')

# @login_required
# def register(request):
#     if request.method == "POST":
#         username = request.POST['username']
#         email = request.POST['email']
#         password = request.POST['password']
#         role = request.POST['role']
#         if RealEstateUser.objects.filter(username=username).exists():
#             messages.error(request, "⚠️ Username already exists. Please choose a different username.")
#             return redirect('register')
#         if RealEstateUser.objects.filter(email=email).exists():
#             messages.error(request, "⚠️ Email already exists. Please choose a different email.")
#             return redirect('register')
#         user = RealEstateUser.objects.create_user(username=username, email=email, password=password, role=role)
#         user.save()
#         messages.success(request, "✅ Registration successful! You can now log in.")
#         return redirect('login')
#     return render(request, 'admin/register.html')

def send_otp(email):
    otp=random.randint(100000,999999)
    send_mail("Your OTP Code",f"Your OTP is {otp}", "crisislinker@gmail.com", [email],fail_silently=False)
    return otp


def password_reset_request(request):
    if request.method=="POST":
        email=request.POST['email']
        try:
            user=RealEstateUser.objects.get(email=email)
            otp=send_otp(email)
            context={
                'email':email,
                'otp':otp
            }
            return render(request,"public/verify_otp.html",context)
        except RealEstateUser.DoesNotExist:
            messages.error(request,"⚠️ Email address not found!")
            return render(request,'public/password_reset.html')
    else:
        return render(request,'public/password_reset.html')
    
def verify_otp(request):
    if request.method == "POST":
        email = request.POST.get('email')
        otpold = request.POST.get('otp')
        otp = request.POST.get('otp1')

        if otpold == otp:
            request.session['reset_email'] = email
            return redirect('new_password')

        else:
            messages.error(request, '⚠️ Invalid OTP')

    return render(request, 'public/verify_otp.html')


def set_new_password(request):

    email = request.session.get('reset_email')

    if not email:
        messages.error(request, "⚠️ Password reset session expired.")
        return redirect('password_reset')

    if request.method == "POST":

        new_password = request.POST.get('new_password')

        try:
            user = RealEstateUser.objects.get(email=email)

            user.set_password(new_password)
            user.save()

            request.session.pop('reset_email', None)

            messages.success(request,"✅ Password has been reset successfully!")

            return redirect('login')

        except RealEstateUser.DoesNotExist:
            messages.error(request, "⚠️ User not found.")

    return render(request,'public/new_password.html',{'email': email})


@login_required
def add_admin(request):
    if request.method=='POST':
        name=request.POST['name']
        email=request.POST['email']
        role=request.POST['role']
        phone=request.POST['phone']
        department=request.POST['department']
        profile_photo=request.FILES.get('profile_photo')
        designation=request.POST['designation']
        bio=request.POST['bio']
        facebook_link=request.POST['facebook_link']
        linkedin_link=request.POST['linkedin_link']
        instagram_link=request.POST['instagram_link']
        twitter_link=request.POST['twitter_link']
        username=request.POST['username']
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']

        if RealEstateUser.objects.filter(email=email).exists():
            messages.error(request, "⚠️ Email already exists. Please choose a different email.")
            return redirect('add_admin')

        if RealEstateUser.objects.filter(phone=phone).exists():
            messages.error(request, "⚠️ Phone number already exists. Please choose a different phone number.")
            return redirect('add_admin')

        if RealEstateUser.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Username already exists. Please choose a different username.")
            return redirect('add_admin')

        if password != confirm_password:
            messages.error(request, "⚠️ Passwords do not match.")
            return redirect('add_admin')

        RealEstateUser.objects.create_user(name=name, email=email, role=role, phone=phone, department=department, profile_photo=profile_photo, designation=designation, bio=bio, facebook_link=facebook_link, linkedin_link=linkedin_link, instagram_link=instagram_link, twitter_link=twitter_link, username=username, password=password)
        messages.success(request, "✅ Admin account created successfully!")
        send_user(email,username,password)
        return redirect('manage_admins')      
        
    return render(request, "admin/add_admin.html")


@login_required
def manage_admins(request):
    query=request.POST.get('search_content')
    if query:
        # data = RealEstateUser.objects.filter(name__icontains=query OR email__icontains=query)
        data = RealEstateUser.objects.filter(
            Q(role='Admin') &
            (
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
        )
    else:
        data=RealEstateUser.objects.filter(role__iexact="Admin").order_by('-id')
    return render(request,'admin/manage_admins.html',{'emp':data})

@login_required
def edit_admin(request,id):
    data=RealEstateUser.objects.get(id=id)
    if request.method=='POST':
        data.name=request.POST['name']
        data.email=request.POST['email']
        data.role=request.POST['role']
        data.phone=request.POST['phone']
        data.department=request.POST['department']
        data.profile_photo=request.FILES.get('profile_photo')
        data.designation=request.POST['designation']
        data.bio=request.POST['bio']
        data.facebook_link=request.POST['facebook_link']
        data.linkedin_link=request.POST['linkedin_link']
        data.instagram_link=request.POST['instagram_link']
        data.twitter_link=request.POST['twitter_link']
        data.username=request.POST['username']

        data.save()
        return redirect("manage_admins")
    return render(request, 'admin/edit_admin.html',{"form":data})

@login_required
def delete_admin(request,id):
    data=RealEstateUser.objects.get(id=id)
    if request.method=="POST":
        data.delete()
        return redirect("manage_admins")
    return render(request, 'admin/delete_admin.html',{'form':data})



@login_required
def add_agent(request):
    if request.method=='POST':
        name=request.POST['name']
        email=request.POST['email']
        role=request.POST['role']
        phone=request.POST['phone']
        department=request.POST['department']
        profile_photo=request.FILES.get('profile_photo')
        designation=request.POST['designation']
        bio=request.POST['bio']
        facebook_link=request.POST['facebook_link']
        linkedin_link=request.POST['linkedin_link']
        instagram_link=request.POST['instagram_link']
        twitter_link=request.POST['twitter_link']
        username=request.POST['username']
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']

        if RealEstateUser.objects.filter(email=email).exists():
            messages.error(request, "⚠️ Email already exists. Please choose a different email.")
            return redirect('add_agent')

        if RealEstateUser.objects.filter(phone=phone).exists():
            messages.error(request, "⚠️ Phone number already exists. Please choose a different phone number.")
            return redirect('add_agent')

        if RealEstateUser.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Username already exists. Please choose a different username.")
            return redirect('add_agent')

        if password != confirm_password:
            messages.error(request, "⚠️ Passwords do not match.")
            return redirect('add_agent')

        RealEstateUser.objects.create_user(name=name, email=email, role=role, phone=phone, department=department, profile_photo=profile_photo, designation=designation, bio=bio, facebook_link=facebook_link, linkedin_link=linkedin_link, instagram_link=instagram_link, twitter_link=twitter_link, username=username, password=password)
        messages.success(request, "✅ Admin account created successfully!")
        send_user(email,username,password)
        return redirect('manage_agents')      
        
    return render(request, "admin/add_agent.html")


def send_user(email,username,password):
    send_mail("Your Account is created",f"Congrats!!! Your account is Successfully created. Your username is {username} and password is {password}", "crisislinker@gmail.com", [email],fail_silently=False)


@login_required
def manage_agents(request):
    query=request.POST.get('search_content')
    if query:
        # data = RealEstateUser.objects.filter(name__icontains=query OR email__icontains=query)
        data = RealEstateUser.objects.filter(
            Q(role='Agent') &
            (
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
        )
    else:
        data=RealEstateUser.objects.filter(role__iexact="Agent").order_by('-id')
    return render(request,'admin/manage_agents.html',{'emp':data})

@login_required
def edit_agent(request,id):
    data=RealEstateUser.objects.get(id=id)
    if request.method=='POST':
        data.name=request.POST['name']
        data.email=request.POST['email']
        data.role=request.POST['role']
        data.phone=request.POST['phone']
        data.department=request.POST['department']
        data.profile_photo=request.FILES.get('profile_photo')
        data.designation=request.POST['designation']
        data.bio=request.POST['bio']
        data.facebook_link=request.POST['facebook_link']
        data.linkedin_link=request.POST['linkedin_link']
        data.instagram_link=request.POST['instagram_link']
        data.twitter_link=request.POST['twitter_link']
        data.username=request.POST['username']

        data.save()
        return redirect("manage_agents")
    return render(request, 'admin/edit_agent.html',{"form":data})

@login_required
def delete_agent(request,id):
    data=RealEstateUser.objects.get(id=id)
    if request.method=="POST":
        data.delete()
        return redirect("manage_agents")
    return render(request, 'admin/delete_agent.html',{'form':data})


@login_required
def add_property_category(request):
    if request.method=="POST":
        category_name=request.POST['category_name']
        if PropertyCategory.objects.filter(category_name=category_name).exists():
            messages.error(request, "⚠️ Property Category already exists.")
            return redirect('add_property_category')
        else:
            PropertyCategory.objects.create(category_name=category_name)
            messages.success(request, "✅ Property Category created successfully!")
            return redirect('manage_property_categories')
    return render(request,"admin/add_property_category.html")


@login_required
def manage_property_categories(request):
    if request.method=='POST': 
        query=request.POST['search_content']
        if query:
            data=PropertyCategory.objects.filter(category_name__icontains=query)
    else:
        data=PropertyCategory.objects.order_by('-id')
    return render(request,"admin/manage_property_categories.html",{'emp':data})


@login_required
def edit_property_category(request,id):
    data=PropertyCategory.objects.get(id=id)
    if request.method=='POST':
        data.category_name=request.POST['category_name']
        data.save()
        return redirect('manage_property_categories')
    return render(request,"admin/edit_property_category.html",{'form':data})


@login_required
def delete_property_category(request,id):
    data=PropertyCategory.objects.get(id=id)
    if request.method=='POST':
        data.delete()
        return redirect('manage_property_categories')
    return render(request,'admin/delete_property_category.html',{'form':data})


@login_required
def add_property(request):
    if request.method=='POST':
        last_property = Property.objects.order_by('-id').first()
        if last_property:
            next_id = last_property.id + 1
        else:
            next_id = 1
        property_code = str(next_id).zfill(5)
        title=request.POST['title']
        category = PropertyCategory.objects.get(id=request.POST['category'])
        agent = RealEstateUser.objects.get(id=request.POST['agent'])
        property_type=request.POST['property_type']
        location=request.POST['location']
        featured_property = request.POST.get('featured_property') == 'True'
        status=request.POST['status']

        if Property.objects.filter(property_code=property_code).exists():
            messages.error(request, "⚠️ Property Code already exists.")
            return redirect('add_property')


        Property.objects.create(property_code=property_code, title=title, category=category, agent=agent, property_type=property_type, location=location, featured_property=featured_property, status=status)
        messages.success(request, "✅ Property added successfully!")
        return redirect('manage_properties')

    categories = PropertyCategory.objects.all()
    agents = RealEstateUser.objects.filter(role='Agent')
    return render(request,"admin/add_property.html",{'categories': categories,'agents': agents})


@login_required
def manage_properties(request):
    if request.method=='POST':
        query=request.POST['search_content']
        if query:
            data=Property.objects.filter(Q(property_code__icontains=query) |Q(title__icontains=query))
    else:
        data=Property.objects.order_by('-id')
    return render(request,"admin/manage_properties.html",{'emp':data})


@login_required
def edit_property(request,id):
    data=Property.objects.get(id=id)
    if request.method=='POST':
        data.title=request.POST['title']
        data.category = PropertyCategory.objects.get(id=request.POST['category'])
        data.agent = RealEstateUser.objects.get(id=request.POST['agent'])
        data.property_type=request.POST['property_type']
        data.location=request.POST['location']
        data.status=request.POST['status']
        data.save()
        messages.success(request, "✅ Property updated successfully!")
        return redirect('manage_properties')

    categories = PropertyCategory.objects.all()
    agents = RealEstateUser.objects.filter(role='Agent')
    return render(request,'admin/edit_property.html',{'form':data,'categories': categories,'agents': agents})

@login_required
def delete_property(request,id):
    data=Property.objects.get(id=id)
    if request.method=='POST':
        data.delete()
        messages.success(request, "✅ Property deleted successfully!")
        return redirect('manage_properties')
    return render(request,'admin/delete_property.html',{'form':data})


@login_required
def manage_inquiries(request):
    if request.method=='POST': 
            query=request.POST['search_content']
            if query:
                data=CustomerInquiry.objects.filter(Q(inquiry_code__icontains=query) |Q(subject__icontains=query) |Q(email__icontains=query))
    else:
        data=CustomerInquiry.objects.order_by('-id')
    return render(request,"admin/manage_inquiries.html",{'emp':data})


@login_required
def view_inquiry(request,id):
    data=CustomerInquiry.objects.get(id=id)
    return render(request,'admin/view_inquiry.html',{'form':data})


@login_required
def assign_inquiry(request, id):

    data = CustomerInquiry.objects.get(id=id)
    if request.method == 'POST':
        agent_id = request.POST['assigned_to']
        data.assigned_to = RealEstateUser.objects.get(id=agent_id)
        data.status = 'Assigned'
        data.save()
        messages.success(request, "✅ Inquiry assigned successfully!")
        return redirect('manage_inquiries')

    agents = RealEstateUser.objects.filter(role='Agent')
    return render(request,'admin/assign_inquiry.html',{'form': data,'agents': agents})



@login_required
def reply_inquiry(request,id):
    data=CustomerInquiry.objects.get(id=id)
    if request.method=='POST':
        reply=request.POST['reply']
        data.reply = reply
        data.status = 'Replied'
        data.save()
        send_inquiry(data.inquiry_code,data.email,data.subject,reply)
        messages.success(request, "✅ Reply sent successfully!")
        return redirect('manage_inquiries')
    return render(request,'admin/reply_inquiry.html')


def send_inquiry(inquiry_code,email,subject,reply):
    send_mail(f"Reply to your inquiry {inquiry_code}",f"Your inquiry with subject '{subject}' has been replied.\n\n Here is the reply:\n {reply}\n\n Thank you!", "crisislinker@gmail.com", [email], fail_silently=False)
   

@login_required
def manage_featured_properties(request):
    if request.method=='POST': 
            query=request.POST['search_content']
            if query:
                data=Property.objects.filter(Q(property_code__icontains=query) |Q(title__icontains=query) |Q(location__icontains=query), featured_property=True)
    else:
        data=Property.objects.order_by('-id')
    return render(request,"admin/manage_featured_properties.html",{'emp':data})

@login_required
def edit_featured_property(request,id):
    data=Property.objects.get(id=id)
    if request.method=='POST':
        update_featured_property = request.POST.get('featured_property')
        if update_featured_property == 'Yes':
            data.featured_property = True
        else:
            data.featured_property = False
        data.save()
        messages.success(request, "✅ Featured property updated successfully!")
        return redirect('manage_featured_properties')
    return render(request,'admin/edit_featured_property.html',{'form':data})



@login_required
def reports_statistics(request):

    total_properties = Property.objects.count()

    total_agents = RealEstateUser.objects.filter(role='Agent').count()

    total_inquiries = CustomerInquiry.objects.count()

    featured_properties = Property.objects.filter(
        featured_property=True
    ).count()

    available_properties = Property.objects.filter(
        status='Available'
    ).count()

    sold_properties = Property.objects.filter(
        status='Sold'
    ).count()

    rented_properties = Property.objects.filter(
        status='Rented'
    ).count()

    pending_inquiries = CustomerInquiry.objects.filter(
        status='Pending'
    ).count()

    replied_inquiries = CustomerInquiry.objects.filter(
        status='Replied'
    ).count()

    categories = PropertyCategory.objects.annotate(
        property_count=Count('property')
    )

    context = {
        'total_properties': total_properties,
        'total_agents': total_agents,
        'total_inquiries': total_inquiries,
        'featured_properties': featured_properties,

        'available_properties': available_properties,
        'sold_properties': sold_properties,
        'rented_properties': rented_properties,

        'pending_inquiries': pending_inquiries,
        'replied_inquiries': replied_inquiries,

        'categories': categories,
    }

    return render(request,'admin/reports_statistics.html',context)


@login_required
def export_excel_report(request):

    properties = Property.objects.all()

    total_properties = properties.count()

    total_agents = RealEstateUser.objects.filter(
        role='Agent'
    ).count()

    total_inquiries = CustomerInquiry.objects.count()

    featured_properties = properties.filter(
        featured_property=True
    ).count()

    available_properties = properties.filter(
        status='Available'
    ).count()

    sold_properties = properties.filter(
        status='Sold'
    ).count()

    rented_properties = properties.filter(
        status='Rented'
    ).count()

    pending_inquiries = CustomerInquiry.objects.filter(
        status='Pending'
    ).count()

    replied_inquiries = CustomerInquiry.objects.filter(
        status='Replied'
    ).count()


    # Create workbook

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = "Statistics"


    # Title

    worksheet["A1"] = "GOLDEN VISION REAL ESTATE"

    worksheet["A1"].font = Font(
        bold=True,
        size=18
    )

    worksheet.merge_cells("A1:B1")


    worksheet["A2"] = "Reports & Statistics"

    worksheet["A2"].font = Font(
        bold=True,
        size=14
    )

    worksheet.merge_cells("A2:B2")


    # Statistics

    data = [

        ["Metric", "Value"],

        ["Total Properties", total_properties],

        ["Total Agents", total_agents],

        ["Total Inquiries", total_inquiries],

        ["Featured Properties", featured_properties],

        ["Available Properties", available_properties],

        ["Sold Properties", sold_properties],

        ["Rented Properties", rented_properties],

        ["Pending Inquiries", pending_inquiries],

        ["Replied Inquiries", replied_inquiries],

    ]


    for row in data:

        worksheet.append(row)


    # Header styling

    for cell in worksheet[3]:

        cell.font = Font(
            bold=True
        )

        cell.fill = PatternFill(
            start_color="D9EAF7",
            end_color="D9EAF7",
            fill_type="solid"
        )


    # Column width

    worksheet.column_dimensions["A"].width = 30

    worksheet.column_dimensions["B"].width = 20


    # Second sheet - Property Details

    property_sheet = workbook.create_sheet(
        "Property Details"
    )


    property_headers = [

        "Property Code",
        "Title",
        "Category",
        "Agent",
        "Property Type",
        "Price",
        "Location",
        "Status",
        "Featured"

    ]


    property_sheet.append(
        property_headers
    )


    for property in properties:

        agent_name = (
            property.agent.name
            if property.agent
            else "Not Assigned"
        )

        property_sheet.append([

            property.property_code,

            property.title,

            property.category.category_name,

            agent_name,

            property.property_type,

            property.price,

            property.location,

            property.status,

            "Yes" if property.featured_property else "No"

        ])


    # Style property header

    for cell in property_sheet[1]:

        cell.font = Font(
            bold=True
        )

        cell.fill = PatternFill(
            start_color="D9EAF7",
            end_color="D9EAF7",
            fill_type="solid"
        )


    # Column widths

    widths = {

        "A": 18,
        "B": 30,
        "C": 20,
        "D": 25,
        "E": 15,
        "F": 15,
        "G": 30,
        "H": 15,
        "I": 12

    }


    for column, width in widths.items():

        property_sheet.column_dimensions[
            column
        ].width = width


    # Response

    response = HttpResponse(

        content_type=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="Golden_Vision_Report.xlsx"'


    workbook.save(response)

    return response


@login_required
def export_pdf_report(request):

    properties = Property.objects.all()

    total_properties = properties.count()

    total_agents = RealEstateUser.objects.filter(
        role='Agent'
    ).count()

    total_inquiries = CustomerInquiry.objects.count()

    featured_properties = properties.filter(
        featured_property=True
    ).count()

    available_properties = properties.filter(
        status='Available'
    ).count()

    sold_properties = properties.filter(
        status='Sold'
    ).count()

    rented_properties = properties.filter(
        status='Rented'
    ).count()

    pending_inquiries = CustomerInquiry.objects.filter(
        status='Pending'
    ).count()

    replied_inquiries = CustomerInquiry.objects.filter(
        status='Replied'
    ).count()


    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = 'attachment; filename="Golden_Vision_Report.pdf"'


    document = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )


    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(

        'TitleStyle',

        parent=styles['Title'],

        alignment=TA_CENTER,

        fontSize=20,

        spaceAfter=10

    )


    subtitle_style = ParagraphStyle(

        'SubtitleStyle',

        parent=styles['Heading2'],

        alignment=TA_CENTER,

        fontSize=14,

        spaceAfter=20

    )


    normal_style = styles['Normal']


    elements = []


    # Title

    elements.append(
        Paragraph(
            "GOLDEN VISION REAL ESTATE",
            title_style
        )
    )


    elements.append(
        Paragraph(
            "Reports & Statistics",
            subtitle_style
        )
    )


    elements.append(
        Spacer(1, 10)
    )


    # Summary table

    summary_data = [

        ["Metric", "Value"],

        ["Total Properties", total_properties],

        ["Total Agents", total_agents],

        ["Total Inquiries", total_inquiries],

        ["Featured Properties", featured_properties],

        ["Available Properties", available_properties],

        ["Sold Properties", sold_properties],

        ["Rented Properties", rented_properties],

        ["Pending Inquiries", pending_inquiries],

        ["Replied Inquiries", replied_inquiries],

    ]


    summary_table = Table(

        summary_data,

        colWidths=[300, 120]

    )


    summary_table.setStyle(

        TableStyle([

            (
                'BACKGROUND',
                (0, 0),
                (-1, 0),
                colors.HexColor("#D9EAF7")
            ),

            (
                'TEXTCOLOR',
                (0, 0),
                (-1, 0),
                colors.black
            ),

            (
                'FONTNAME',
                (0, 0),
                (-1, 0),
                'Helvetica-Bold'
            ),

            (
                'ALIGN',
                (1, 1),
                (-1, -1),
                'CENTER'
            ),

            (
                'GRID',
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                'FONTNAME',
                (0, 1),
                (-1, -1),
                'Helvetica'
            ),

            (
                'FONTSIZE',
                (0, 0),
                (-1, -1),
                10
            ),

            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                8
            ),

            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                8
            ),

        ])

    )


    elements.append(
        summary_table
    )


    elements.append(
        Spacer(1, 30)
    )


    # Property details heading

    elements.append(

        Paragraph(
            "Property Details",
            styles['Heading2']
        )

    )


    elements.append(
        Spacer(1, 10)
    )


    property_data = [

        [
            "Code",
            "Title",
            "Category",
            "Type",
            "Price",
            "Status"
        ]

    ]


    for property in properties:

        property_data.append([

            property.property_code,

            property.title,

            property.category.category_name,

            property.property_type,

            str(property.price)
            if property.price
            else "-",

            property.status

        ])


    property_table = Table(

        property_data,

        colWidths=[
            60,
            120,
            80,
            50,
            70,
            60
        ],

        repeatRows=1

    )


    property_table.setStyle(

        TableStyle([

            (
                'BACKGROUND',
                (0, 0),
                (-1, 0),
                colors.HexColor("#D9EAF7")
            ),

            (
                'FONTNAME',
                (0, 0),
                (-1, 0),
                'Helvetica-Bold'
            ),

            (
                'FONTSIZE',
                (0, 0),
                (-1, -1),
                7
            ),

            (
                'GRID',
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),

            (
                'VALIGN',
                (0, 0),
                (-1, -1),
                'MIDDLE'
            ),

            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                6
            ),

            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                6
            ),

        ])

    )


    elements.append(
        property_table
    )


    document.build(elements)


    return response



@login_required
def assigned_properties(request):
    if request.method=='POST':
        query=request.POST['search_content']
        if query:
            data = Property.objects.filter(agent=request.user).filter(Q(property_code__icontains=query) |Q(title__icontains=query))
    else:
        data = Property.objects.filter(agent=request.user).order_by('-id')
    return render(request,"agent/assigned_properties.html",{'emp':data})



@login_required
def view_property(request, id):

    data = Property.objects.get(id=id,agent=request.user)

    missing_fields = []

    if not data.description:
        missing_fields.append("Description")

    if not data.price:
        missing_fields.append("Price")

    if not data.bedrooms:
        missing_fields.append("Bedrooms")

    if not data.bathrooms:
        missing_fields.append("Bathrooms")

    if not data.area_sqft:
        missing_fields.append("Area (Sq Ft)")

    if not data.video_tour:
        missing_fields.append("Video Tour")

    if not PropertyImage.objects.filter(property=data).exists():
        missing_fields.append("Property Images")

    return render(request,'agent/view_property.html',{'form': data,'missing_fields': missing_fields})


@login_required
def agent_edit_property(request,id):
    data=Property.objects.get(id=id,agent=request.user)
    if request.method=='POST':
        print(request.POST)
        print("PRICE =", request.POST.get('price'))

        data.title=request.POST['title']
        data.category = PropertyCategory.objects.get(id=request.POST['category'])
        data.property_type=request.POST['property_type']
        data.description=request.POST['description']
        data.price=request.POST['price']
        data.location=request.POST['location']
        data.bedrooms=request.POST['bedrooms']
        data.bathrooms=request.POST['bathrooms']
        data.area_sqft=request.POST['area_sqft']
        data.status=request.POST['status']
        video_tour = request.FILES.get('video_tour')
        if video_tour:
            data.video_tour = video_tour

        images = request.FILES.getlist('property_images')
        for image in images:
            PropertyImage.objects.create(
                property=data,
                image=image
            )
        data.save()
        messages.success(request, "✅ Property updated successfully!")
        return redirect('agent_manage_properties')

    categories = PropertyCategory.objects.all()
    return render(request,'agent/agent_edit_property.html',{'form':data,'categories': categories})


@login_required
def delete_property_image(request,id):

    image = PropertyImage.objects.get(
        id=id,
        property__agent=request.user
    )

    property_id = image.property.id

    image.delete()

    messages.success(
        request,
        "✅ Image deleted successfully!"
    )

    return redirect(
        'agent_edit_property',
        id=property_id
    )


@login_required
def agent_manage_properties(request):
    if request.method=='POST':
        query=request.POST['search_content']
        if query:
            data=Property.objects.filter(agent=request.user).filter(Q(property_code__icontains=query) |Q(title__icontains=query))
    else:
        data=Property.objects.filter(agent=request.user).order_by('-id')
    return render(request,"agent/agent_manage_properties.html",{'emp':data})


@login_required
def agent_delete_property(request,id):
    data=Property.objects.get(id=id,agent=request.user)
    if request.method=='POST':
        data.delete()
        messages.success(request, "✅ Property deleted successfully!")
        return redirect('agent_manage_properties')
    return render(request,'agent/agent_delete_property.html',{'form':data})


@login_required
def add_property_with_image(request):
    if request.method=='POST':
            last_property = Property.objects.order_by('-id').first()
            if last_property:
                next_id = last_property.id + 1
            else:
                next_id = 1
            property_code = str(next_id).zfill(5)
            title=request.POST['title']
            category = PropertyCategory.objects.get(id=request.POST['category'])
            agent = request.user
            description=request.POST['description']
            price=request.POST['price']
            bedrooms=request.POST['bedrooms']
            bathrooms=request.POST['bathrooms']
            area_sqft=request.POST['area_sqft']
            video_tour = request.FILES.get('video_tour')
            property_type=request.POST['property_type']
            location=request.POST['location']
            featured_property = request.POST.get('featured_property') == 'True'
            status=request.POST['status']
    
            if Property.objects.filter(property_code=property_code).exists():
                messages.error(request, "⚠️ Property Code already exists.")
                return redirect('add_property_with_image')
    
    
            new_property = Property.objects.create(property_code=property_code, title=title, category=category, agent=agent,description=description, price=price, bedrooms=bedrooms, bathrooms=bathrooms, area_sqft=area_sqft, video_tour=video_tour, property_type=property_type, location=location, featured_property=featured_property, status=status)
            images = request.FILES.getlist('property_images')

            for image in images:
                PropertyImage.objects.create(
                    property=new_property,
                    image=image
                )
            messages.success(request, "✅ Property added successfully!")
            return redirect('agent_manage_properties')
    
    categories = PropertyCategory.objects.all()
    return render(request,"agent/add_property_with_image.html",{'categories': categories})


@login_required
def agent_manage_inquiries(request):
    if request.method=='POST': 
            query=request.POST['search_content']
            if query:
                data=CustomerInquiry.objects.filter(Q(inquiry_code__icontains=query) |Q(subject__icontains=query) |Q(email__icontains=query))
    else:
        data=CustomerInquiry.objects.filter(assigned_to=request.user).order_by('-id')
    return render(request,"agent/agent_manage_inquiries.html",{'emp':data})


@login_required
def agent_view_inquiry(request,id):
    data=CustomerInquiry.objects.get(id=id)
    return render(request,'agent/agent_view_inquiry.html',{'form':data})



@login_required
def agent_reply_inquiry(request,id):
    data=CustomerInquiry.objects.get(id=id)
    if request.method=='POST':
        reply=request.POST['reply']
        data.reply = reply
        data.status = 'Replied'
        data.save()
        send_inquiry(data.inquiry_code,data.email,data.subject,reply)
        messages.success(request, "✅ Reply sent successfully!")
        return redirect('agent_manage_inquiries')
    return render(request,'agent/agent_reply_inquiry.html')


@login_required
def agent_property_status(request):
    data=Property.objects.filter(agent=request.user).order_by('-created_at')
    return render(request,'agent/agent_property_status.html',{'form':data})



@login_required
def agent_sales_summary(request):

    properties = Property.objects.filter(agent=request.user)

    sold_properties = properties.filter(status='Sold').order_by('-created_at')

    total_sales_value = (sold_properties.aggregate(total=Sum('price'))['total'] or 0)

    total_sold = sold_properties.count()
    total_available = properties.filter(status='Available').count()
    total_rented = properties.filter(status='Rented').count()

    context = {
        'sold_properties': sold_properties,
        'total_sales_value': total_sales_value,
        'total_sold': total_sold,
        'total_available': total_available,
        'total_rented': total_rented,
    }

    return render(request,'agent/agent_sales_summary.html',context)




@login_required
def download_property_package(request, id):
    # Agents can download only their own properties.
    data = get_object_or_404(
        Property,
        id=id,
        agent=request.user
    )

    # Create the folder name from the property title.
    folder_name = slugify(data.title) or f"property-{data.id}"

    # -------------------------------
    # 1. Create the property PDF
    # -------------------------------
    pdf_buffer = BytesIO()

    pdf = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PropertyTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#243B35"),
        spaceAfter=18
    )

    label_style = ParagraphStyle(
        "PropertyLabel",
        parent=styles["BodyText"],
        leading=15,
        spaceAfter=6,
        wordWrap="CJK"
    )

    def safe(value):
        return escape(str(value if value not in (None, "") else "Not provided"))

    property_details = [
        ("Property Code", data.property_code),
        ("Title", data.title),
        ("Category", data.category),
        ("Property Type", data.property_type),
        ("Availability Status", data.status),
        ("Price", f"{data.price}" if data.price is not None else "Not provided"),
        ("Location", data.location),
        ("Bedrooms", data.bedrooms),
        ("Bathrooms", data.bathrooms),
        ("Area (sq. ft.)", data.area_sqft),
        ("Description", data.description),
        (
            "Assigned Agent",
            data.agent.get_full_name() or data.agent.username
            if data.agent else "Not assigned"
        ),
        ("Featured Property", "Yes" if data.featured_property else "No"),
        (
            "Created Date",
            data.created_at.strftime("%d %B %Y")
            if data.created_at else "Not provided"
        ),
    ]

    story = [
        Paragraph("GOLDEN VISION", title_style),
        Paragraph("Property Details", styles["Heading2"]),
        Spacer(1, 8),
    ]

    table_data = [["Field", "Details"]]

    for label, value in property_details:
        table_data.append([
            Paragraph(safe(label), label_style),
            Paragraph(safe(value), label_style)
        ])

    details_table = Table(
        table_data,
        colWidths=[48 * mm, 112 * mm],
        repeatRows=1
    )

    details_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243B35")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6D6D6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F3F2EE")),
    ]))

    story.append(details_table)
    pdf.build(story)
    pdf_buffer.seek(0)

    # -------------------------------
    # 2. Create the ZIP archive
    # -------------------------------
    zip_buffer = BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        # Add the PDF inside the property folder.
        archive.writestr(
            f"{folder_name}/property_details.pdf",
            pdf_buffer.getvalue()
        )

        # Add every image uploaded for this property.
        for image_obj in data.images.all():
            if image_obj.image:
                try:
                    image_obj.image.open("rb")
                    try:
                        archive.writestr(
                            f"{folder_name}/Images/{os.path.basename(image_obj.image.name)}",
                            image_obj.image.read()
                        )
                    finally:
                        image_obj.image.close()
                except (OSError, ValueError):
                    # Skip an image if its file cannot be accessed.
                    pass

        # Add the property video tour, if available.
        if data.video_tour:
            try:
                data.video_tour.open("rb")
                try:
                    archive.writestr(
                        f"{folder_name}/Videos/{os.path.basename(data.video_tour.name)}",
                        data.video_tour.read()
                    )
                finally:
                    data.video_tour.close()
            except (OSError, ValueError):
                # Skip the video if its file cannot be accessed.
                pass

    # -------------------------------
    # 3. Send the ZIP for download
    # -------------------------------
    zip_buffer.seek(0)

    response = HttpResponse(
        zip_buffer.getvalue(),
        content_type="application/zip"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{folder_name}.zip"'
    )

    return response



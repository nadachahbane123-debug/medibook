from django.db import models
from accounts.models import User


class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🩺')
    keywords = models.TextField(blank=True, help_text='Mots-clés pour l\'IA, séparés par des virgules')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Spécialité'
        verbose_name_plural = 'Spécialités'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_keywords_list(self):
        return [k.strip() for k in self.keywords.split(',') if k.strip()]


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, related_name='doctors')
    additional_specialties = models.ManyToManyField(Specialty, blank=True, related_name='secondary_doctors')
    license_number = models.CharField(max_length=50, unique=True)
    phone_professional = models.CharField(max_length=20)
    cabinet_address = models.TextField()
    bio = models.TextField(blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Médecin'
        verbose_name_plural = 'Médecins'

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    def update_rating(self):
        from appointments.models import Review
        reviews = Review.objects.filter(appointment__doctor=self)
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg, 2)
            self.total_reviews = reviews.count()
            self.save(update_fields=['rating', 'total_reviews'])

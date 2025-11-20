from datetime import date, timedelta

from django.core.management import BaseCommand

from attendance.models import EmployeeSchedule, ScheduleTemplate
from staff.models import Employee, Position


DEFAULT_TEMPLATES = {
    'Кладовщик': {
        'mon': ['07:30', '16:30'],
        'tue': ['07:30', '16:30'],
        'wed': ['07:30', '16:30'],
        'thu': ['07:30', '16:30'],
        'fri': ['07:30', '16:30'],
    },
    'Продавец': {
        'mon': ['08:30', '17:30'],
        'tue': ['08:30', '17:30'],
        'wed': ['08:30', '17:30'],
        'thu': ['12:00', '21:00'],
        'fri': ['12:00', '21:00'],
        'sat': ['10:00', '18:00'],
        'sun': ['10:00', '18:00'],
    },
    'Товаровед': {
        'mon': ['08:00', '17:00'],
        'tue': ['08:00', '17:00'],
        'wed': ['08:00', '17:00'],
        'thu': ['08:00', '17:00'],
        'fri': ['08:00', '17:00'],
    },
    'Директор магазина': {
        'mon': ['09:00', '18:00'],
        'tue': ['09:00', '18:00'],
        'wed': ['09:00', '18:00'],
        'thu': ['09:00', '18:00'],
        'fri': ['09:00', '18:00'],
    },
}


class Command(BaseCommand):
    help = 'Creates schedule templates for key positions and assigns them to current employees.'

    def _find_position(self, canonical_name: str) -> Position | None:
        position = Position.objects.filter(name__iexact=canonical_name).first()
        if position:
            return position
        keywords = canonical_name.split()
        query = Position.objects.all()
        for keyword in keywords:
            query = query.filter(name__icontains=keyword)
        position = query.first()
        if position:
            return position
        # fallback: partial match
        return Position.objects.filter(name__icontains=canonical_name[:5]).first()

    def handle(self, *args, **options):
        effective_from = date.today() - timedelta(days=date.today().weekday())
        created_templates = 0
        assignments = 0

        for position_name, weekdays in DEFAULT_TEMPLATES.items():
            position = self._find_position(position_name)
            if not position:
                self.stdout.write(self.style.WARNING(f'Position "{position_name}" not found, skipping.'))
                continue
            template, created = ScheduleTemplate.objects.get_or_create(
                name=f'{position.name} (стандарт)',
                defaults={
                    'position': position,
                    'weekdays': weekdays,
                },
            )
            if created:
                created_templates += 1
            employees = Employee.objects.filter(position=position, status=Employee.ACTIVE)
            for employee in employees:
                EmployeeSchedule.objects.update_or_create(
                    employee=employee,
                    defaults={
                        'template': template,
                        'effective_from': effective_from,
                        'notes': 'Автопривязка шаблона',
                    },
                )
                assignments += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Готово: {created_templates} шаблон(ов) создано, {assignments} сотрудников получили расписания.'
            )
        )



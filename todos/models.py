from django.db import models

from accounts.models import Member


class Category(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='categories',
        help_text='카테고리 소유자',
    )
    name = models.CharField(max_length=50, help_text='카테고리 이름')

    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리'
        ordering = ['name']
        unique_together = [['member', 'name']]

    def __str__(self):
        return self.name


class Todo(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', '할 일'
        IN_PROGRESS = 'in_progress', '진행 중'
        DONE = 'done', '완료'

    member = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, related_name='todos'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='todos',
        help_text='할 일의 카테고리',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        help_text='할 일의 현재 상태',
    )
    due_date = models.DateField(
        null=True, blank=True, help_text='할 일의 기한일 (선택 사항)'
    )

    def __str__(self):
        return self.title

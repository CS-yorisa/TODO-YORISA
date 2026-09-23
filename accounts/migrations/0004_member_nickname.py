from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_member_withdrawn_at_alter_member_email_and_more'),
    ]

    operations = [
        # 기존 회원 행은 빈 문자열로 채우고, 이후에는 기본값 없이 필수 입력으로 둔다.
        migrations.AddField(
            model_name='member',
            name='nickname',
            field=models.CharField(default='', max_length=30, verbose_name='닉네임'),
            preserve_default=False,
        ),
    ]

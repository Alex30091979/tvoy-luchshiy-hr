"""Seed: 10 Moscow + 10 RF clusters with keywords."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from libs.common.database import session_scope
from libs.common.models.db_models import Cluster, Keyword, Setting

MOSCOW_CLUSTERS = [
    ("Бухгалтер в офис Москва", "moscow", "buhgalter-ofis-moscow", [
        ("бухгалтер в офис москва", 720),
        ("подбор бухгалтера москва", 480),
        ("бухгалтер на удаленку москва", 390),
    ]),
    ("HR менеджер подбор Москва", "moscow", "hr-manager-podbor-moscow", [
        ("hr менеджер подбор персонала москва", 590),
        ("рекрутер москва", 880),
        ("специалист по подбору москва", 320),
    ]),
    ("Юрист в компанию Москва", "moscow", "yurist-kompaniya-moscow", [
        ("юрист в компанию москва", 640),
        ("корпоративный юрист москва", 480),
        ("юрист по договорам москва", 390),
    ]),
    ("Маркетолог B2B Москва", "moscow", "marketing-b2b-moscow", [
        ("маркетолог b2b москва", 420),
        ("digital маркетолог москва", 590),
        ("маркетинг менеджер москва", 320),
    ]),
    ("Офис менеджер ассистент Москва", "moscow", "ofis-assistent-moscow", [
        ("офис менеджер москва", 480),
        ("ассистент руководителя москва", 720),
        ("секретарь офис москва", 390),
    ]),
    ("Менеджер по продажам Москва", "moscow", "manager-prodazhi-moscow", [
        ("менеджер по продажам москва", 1000),
        ("менеджер по продажам b2b москва", 480),
        ("отдел продаж подбор москва", 260),
    ]),
    ("Подбор бухгалтера средний бизнес", "moscow", "podbor-buhgaltera-sredniy-biznes", [
        ("подбор бухгалтера средний бизнес", 210),
        ("бухгалтер средняя компания москва", 170),
    ]),
    ("Подбор HR специалиста Москва", "moscow", "podbor-hr-specialist-moscow", [
        ("подбор hr специалиста москва", 320),
        ("hr бизнес партнер москва", 390),
    ]),
    ("Юрист штатный Москва", "moscow", "yurist-shtatnyy-moscow", [
        ("штатный юрист москва", 480),
        ("юрист в штат москва", 260),
    ]),
    ("Маркетинг директор Москва", "moscow", "marketing-director-moscow", [
        ("директор по маркетингу москва", 590),
        ("head of marketing москва", 320),
    ]),
]

RF_CLUSTERS = [
    ("Бухгалтер удаленно РФ", "rf", "buhgalter-udalenno-rf", [
        ("бухгалтер удаленно россия", 880),
        ("бухгалтер на удаленке", 720),
    ]),
    ("Рекрутинг подбор РФ", "rf", "rekruiting-podbor-rf", [
        ("рекрутинг подбор персонала россия", 480),
        ("подбор персонала удаленно", 390),
    ]),
    ("Юрист компания РФ", "rf", "yurist-kompaniya-rf", [
        ("юрист в компанию россия", 590),
        ("корпоративный юрист удаленно", 260),
    ]),
    ("Маркетолог удаленно РФ", "rf", "marketing-udalenno-rf", [
        ("маркетолог удаленно россия", 480),
        ("digital маркетолог удаленно", 320),
    ]),
    ("Ассистент удаленно РФ", "rf", "assistent-udalenno-rf", [
        ("ассистент удаленно россия", 390),
        ("офис менеджер удаленно", 320),
    ]),
    ("Менеджер по продажам РФ", "rf", "manager-prodazhi-rf", [
        ("менеджер по продажам россия", 1000),
        ("менеджер по продажам удаленно", 480),
    ]),
    ("Бухгалтер главный РФ", "rf", "buhgalter-glavnyy-rf", [
        ("главный бухгалтер подбор", 720),
        ("главбух найм", 390),
    ]),
    ("HR директор РФ", "rf", "hr-director-rf", [
        ("hr директор подбор", 320),
        ("директор по персоналу найм", 260),
    ]),
    ("Юрист по сделкам РФ", "rf", "yurist-sdelki-rf", [
        ("юрист по сделкам M&A", 210),
        ("юрист договоры компания", 320),
    ]),
    ("SMM маркетолог РФ", "rf", "smm-marketing-rf", [
        ("smm специалист подбор", 480),
        ("контент маркетолог найм", 260),
    ]),
]


def run_seed() -> None:
    with session_scope() as session:
        # Default settings
        for key, value, desc in [
            ("publish_mode", "semi", "auto | semi (AUTO=direct publish, SEMI=draft+approval)"),
            ("dry_run", "true", "Generate without publishing"),
            ("daily_token_quota", "100000", "Max tokens per day"),
            ("articles_per_day", "1", "Max articles per day (MVP limit)"),
            ("moscow_share", "0.7", "Share Moscow vs RF (0..1)"),
        ]:
            from sqlalchemy import select
            from libs.common.models.db_models import Setting
            existing = session.execute(select(Setting).where(Setting.key == key)).scalars().one_or_none()
            if not existing:
                session.add(Setting(key=key, value=value, description=desc))

        # Clusters + keywords
        for name, region, slug, kws in MOSCOW_CLUSTERS + RF_CLUSTERS:
            from sqlalchemy import select
            existing = session.execute(select(Cluster).where(Cluster.slug == slug)).scalars().one_or_none()
            if existing:
                continue
            cluster = Cluster(name=name, region=region, slug=slug, is_active=True, priority=10 if region == "moscow" else 5)
            session.add(cluster)
            session.flush()
            for kw, vol in kws:
                session.add(Keyword(cluster_id=cluster.id, keyword=kw, volume=vol))
    print("Seed done: settings + 10 moscow + 10 rf clusters with keywords.")


if __name__ == "__main__":
    run_seed()

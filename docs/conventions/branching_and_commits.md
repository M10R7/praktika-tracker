# Бұтақтар мен коммиттерді атау келісімі (Branching & Commit Convention)

## 1. Бұтақтау стратегиясы (Git Branching Model)
Жобада жеңілдетілген **Trunk-based / GitHub Flow** стратегиясы қолданылады:
- main — өндірістік дайын (production-ready) және қорғалған негізгі бұтақ. Тікелей commit жасауға тыйым салынады (Direct push prohibited). Тек Pull Request арқылы қосылады.
- develop — біріктіру және сынақтан өткізу (staging) бұтағы.
- Қосалқы бұтақтар develop бұтағынан тармақталып, келесі формат бойынша аталады:

### Бұтақтардың атау форматы:
<түрі>/<тапсырма-нөмірі>-<қысқаша-сипаттама>

Мысалдар:
- Жаңа функционал: eat/PT-12-auth-bin-validation
- Ақауды түзету: ix/PT-34-pdf-margin-overflow
- Құжаттама жазу: docs/PT-02-adr-delivery-model
- Рефакторинг: 
efactor/PT-18-db-connection-pool
- Зерттеу / Spike: spike/PT-09-fastapi-pdf-generation

## 2. Коммиттерді ресімдеу ережесі (Conventional Commits v1.0.0)
Барлық коммиттер ағылшын тілінде, кіші әріптермен және семантикалық префикстермен жазылады:
<түрі>(<құрамдас>): <қысқаша сипаттама>

Негізгі префикстер:
- eat: — пайдаланушы үшін жаңа мүмкіндік (мысалы: eat(student): add bin auto-fill form)
- ix: — жүйедегі қатені түзету (мысалы: ix(contract): fix company head position in pdf)
- docs: — тек құжаттамадағы өзгерістер (мысалы: docs(adr): update ADR-001 delivery model)
- style: — код форматы, бос орындар, нүктелі үтір (логика өзгермейді)
- 
efactor: — функционалды өзгертпей код құрылымын жақсарту
- 	est: — жаңа тесттер қосу немесе барларын түзету
- chore: — жинақтау, тәуелділіктер мен CI/CD баптаулары (мысалы: chore(deps): bump fastapi to 0.110.0)

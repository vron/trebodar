# U-04 rev A – Ljusplaner, belysningsstyrka med all belysning tänd

Eget underlag, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Belysningsstyrkan [lux] med all
belysning tänd och mörkt ute (21 december kl. 22), på fyra blad i ritningsmallen:

| Blad | Mätyta |
|---|---|
| U-04.1 | Plan 1, golvet, med köksbänkarna och ön 0,91 m över golvet |
| U-04.2 | Plan 1, bordshöjd 0,75 m, med köksbänkarna och ön 0,91 m över golvet |
| U-04.3 | Köket, bänkskivorna 0,91 m |
| U-04.4 | Källaren, golvet |

Belysningsstyrkan räknas i renderingen (Blender, Cycles) med armaturernas uppmätta ljusfördelning, reflexerna och
upptaget i rummen; se Ljusplaner i elinstallationens
[README](../../modeller/trebodar/hus/installationer/el/README.md) och `./mod ljusplan` i
[verktyg/modellering](../../verktyg/modellering/README.md). Mätytorna står i modellens
`hus/installationer/el/matytor.py`. Här finns bara projektuppgifterna (`indata.toml`: revision och datum).

## Göra om

```
./bygg U-04        # i repots rot: ljusplanerna ur modellen (cirka en minut), till rapporter/
```

Steget är manuellt: det bygger på hela modellen, så det görs bara när det väljs, inte i `./bygg` eller i GitHub
Actions (som renderingarna). Det kräver Blender och tillverkarnas fotometrifiler i `lokalt/el/` (`./mod el hamta`).
Checka in den nya pdf:en i `rapporter/` och `räknat.json`.

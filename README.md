# FinTech_bot
Телеграм бот, который создает инвестиционные портфели на основе различных стратегий (пока одна). 
Бот дает возможность просматривать историю выбранной стратегии, а так же формирует портфель под текущие параметры.
В данном репозитории показаны отдельные куски кода в связи некоторой коммерческой составляющей.


1)telegram.py - запускает бота
2)main_updater.py - обновление базы данных или ее создание с нуля. **Первый запуск займет очень много времени!!!**


## Запуск бота

Для запуска бота, сначала запустите main_updater.py для выгрузки данных и обсчета необходимых комбинаций.

После этого запускайте telegram.py



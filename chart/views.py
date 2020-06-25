from django.shortcuts import render
from .models import Passenger
from django.db.models import Count, Q

import json  # ***json 임포트 추가***
from django.http import JsonResponse  # for chart_data()
import pandas as pd
import arrow


def home(request):
    return render(request, 'chart/home.html')


def world_population(request):
    return render(request, 'chart/world_population.html')


def ticket_class_view_1(request):  # 방법 1
    dataset = Passenger.objects \
        .values('ticket_class') \
        .annotate(
        survived_count=Count('ticket_class',
                             filter=Q(survived=True)),
        not_survived_count=Count('ticket_class',
                                 filter=Q(survived=False))) \
        .order_by('ticket_class')
    return render(request, 'chart/ticket_class_1.html', {'dataset': dataset})


def ticket_class_view_2(request):  # 방법 2
    dataset = Passenger.objects \
        .values('ticket_class') \
        .annotate(survived_count=Count('ticket_class', filter=Q(survived=True)),
                  not_survived_count=Count('ticket_class', filter=Q(survived=False))) \
        .order_by('ticket_class')

    # 빈 리스트 3종 준비
    categories = list()  # for xAxis
    survived_series = list()  # for series named 'Survived'
    not_survived_series = list()  # for series named 'Not survived'

    # 리스트 3종에 형식화된 값을 등록
    for entry in dataset:
        categories.append('%s Class' % entry['ticket_class'])  # for xAxis
        survived_series.append(entry['survived_count'])  # for series named 'Survived'
        not_survived_series.append(entry['not_survived_count'])  # for series named 'Not survived'

    # json.dumps() 함수로 리스트 3종을 JSON 데이터 형식으로 반환
    return render(request, 'chart/ticket_class_2.html', {
        'categories': json.dumps(categories),
        'survived_series': json.dumps(survived_series),
        'not_survived_series': json.dumps(not_survived_series)
    })


def ticket_class_view_3(request):  # 방법 3
    dataset = Passenger.objects \
        .values('ticket_class') \
        .annotate(survived_count=Count('ticket_class', filter=Q(survived=True)),
                  not_survived_count=Count('ticket_class', filter=Q(survived=False))) \
        .order_by('ticket_class')

    # 빈 리스트 3종 준비 (series 이름 뒤에 '_data' 추가)
    categories = list()  # for xAxis
    survived_series_data = list()  # for series named 'Survived'
    not_survived_series_data = list()  # for series named 'Not survived'

    # 리스트 3종에 형식화된 값을 등록
    for entry in dataset:
        categories.append('%s Class' % entry['ticket_class'])  # for xAxis
        survived_series_data.append(entry['survived_count'])  # for series named 'Survived'
        not_survived_series_data.append(entry['not_survived_count'])  # for series named 'Not survived'

    survived_series = {
        'name': 'Survived',
        'data': survived_series_data,
        'color': 'green'
    }
    not_survived_series = {
        'name': 'Not Survived',
        'data': not_survived_series_data,
        'color': 'red'
    }

    chart = {
        'chart': {'type': 'column'},
        'title': {'text': 'Titanic Survivors by Ticket Class'},
        'xAxis': {'categories': categories},
        'series': [survived_series, not_survived_series]
    }
    dump = json.dumps(chart)

    return render(request, 'chart/ticket_class_3.html', {'chart': dump})


def json_example(request):  # 접속 경로 'json-example/'에 대응하는 뷰
    return render(request, 'chart/json_example.html')


def chart_data(request):  # 접속 경로 'json-example/data/'에 대응하는 뷰
    dataset = Passenger.objects \
        .values('embarked') \
        .exclude(embarked='') \
        .annotate(total=Count('id')) \
        .order_by('-total')

    port_display_name = dict()
    for port_tuple in Passenger.PORT_CHOICES:
        port_display_name[port_tuple[0]] = port_tuple[1]

    chart = {
        'chart': {'type': 'pie'},
        'title': {'text': 'Number of Titanic Passengers by Embarkation Port'},
        'series': [{
            'name': 'Embarkation Port',
            'data': list(map(
                lambda row: {'name': port_display_name[row['embarked']], 'y': row['total']},
                dataset))
        }]
    }
    # [list(map(lambda))](https://wikidocs.net/64)

    return JsonResponse(chart)


def covid19_chart_confirmed(request):
    # 데이터 적재 및 선별
    df = pd.read_csv('https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv',
                     parse_dates=['Date'])
    countries = ['Korea, South', 'Germany', 'United Kingdom', 'US', 'France']
    df = df[df['Country'].isin(countries)]

    # 데이터프레임 준비(확진자)
    df = df.pivot(index='Date', columns='Country', values='Confirmed')

    # 인덱스 조작
    covid = df.reset_index('Date')
    covid.set_index(['Date'], inplace=True)
    covid.columns = countries

    # 날짜별 타임스탬프 값 구하기(arrow 사용)
    date = covid.index
    arrow_date = list()

    for d in date:
        arrow_date.append(arrow.get(d.year, d.month, d.day).timestamp * 1000)
        # http://doc.mindscale.kr/km/python/07.html

    # timestamp 열 추가
    covid['timestamp'] = arrow_date

    # timestamp 열로 인덱스 변경
    covid.reset_index('Date')
    covid.set_index(['timestamp'], inplace=True)
    covid.columns = countries

    # 인구 대비 건수 계산(건/백만명)
    populations = {'Korea, South': 51269185, 'Germany': 83783942,
                   'United Kingdom': 67886011, 'US': 331002651, 'France': 65273511}

    for country in list(covid.columns):
        covid[country] = round(covid[country] / populations[country] * 1000000, 1)
        # 반올림 후 소수 한자리까지 출력

    # 하이차트 그리기 위해 2차원 배열로 데이터 생성
    # [[timestamp, total], [timestamp, total], ...]
    country_data = countries
    for k in range(0, len(countries)):
        #     print(country_data[k])
        timestamp = list(covid.index)
        total = list(covid[countries[k]])
        timestamp_total = list()
        data = list()

        for i in range(0, len(covid.index)):
            timestamp_total.append(timestamp[i])
            timestamp_total.append(total[i])
            data.append(timestamp_total)
            timestamp_total = list()

        country_data[k] = data
    #     print(country_name[k])

    # 하이차트 그리기
    france_series = {
        'name': 'France',
        'data': country_data[0],
        'color': '#7CCBA2'
    }
    germany_series = {
        'name': 'Germany',
        'data': country_data[1],
        'color': '#FCDE9C'
    }
    korea_series = {
        'name': 'Korea, South',
        'data': country_data[2],
        'color': '#045275'
    }
    us_series = {
        'name': 'US',
        'data': country_data[3],
        'color': '#DC3977'
    }
    uk_series = {
        'name': 'United Kingdom',
        'data': country_data[4],
        'color': '#7C1D6F'
    }

    chart = {
        'chart': {'type': 'line'},
        'title': {'text': 'COVID-19 확진자 발생률'},
        'subtitle': {'text': 'Source: Johns Hopkins university Center for System Science and Engineering'},
        'series': [france_series, germany_series, korea_series, us_series, uk_series],

        'xAxis': {
            'type': 'datetime',
            'labels': {
                'format': '{value:%b}'  # https://jsfiddle.net/dLfv2sbd/1/
            },
            'crosshair': 'true',
        },

        'yAxis': {
            'title': {
                'text': '합계 건수',
                'rotation': -90
            },
            'labels': {
                'enabled': 'false',
                'format': '{value}건/백만명'},
            'crosshair': 'true'
        },

        'responsive': {
            'rules': [{
                'condition': {
                    'maxWidth': 500
                },
            }]
        },

        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': 'false'
                },

            }
        },

    }
    dump = json.dumps(chart)

    return render(request, 'chart/covid19_chart_confirmed.html', {'chart': dump})


def covid19_chart_recovered(request):
    # 데이터 적재 및 선별
    df = pd.read_csv('https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv',
                     parse_dates=['Date'])
    countries = ['Korea, South', 'Germany', 'United Kingdom', 'US', 'France']
    df = df[df['Country'].isin(countries)]

    # 데이터프레임 준비(회복자)
    dfr = df.pivot(index='Date', columns='Country', values='Recovered')
    # 데이터프레임 준비(확진자)
    dfc = df.pivot(index='Date', columns='Country', values='Confirmed')

    # 회복자 / 확진자 * 100 으로 회복율 구하기
    df = round((dfr / dfc) * 100, 2)

    # 인덱스 조작
    covid = df.reset_index('Date')
    covid.set_index(['Date'], inplace=True)
    covid.columns = countries

    # 날짜별 타임스탬프 값 구하기(arrow 사용)
    date = covid.index
    arrow_date = list()

    for d in date:
        arrow_date.append(arrow.get(d.year, d.month, d.day).timestamp * 1000)
        # http://doc.mindscale.kr/km/python/07.html

    # timestamp 열 추가
    covid['timestamp'] = arrow_date

    # timestamp 열로 인덱스 변경
    covid.reset_index('Date')
    covid.set_index(['timestamp'], inplace=True)
    covid.columns = countries

    # 하이차트 그리기 위해 2차원 배열로 데이터 생성
    # [[timestamp, total], [timestamp, total], ...]
    country_data = countries
    for k in range(0, len(countries)):
        #     print(country_data[k])
        timestamp = list(covid.index)
        total = list(covid[countries[k]])
        timestamp_total = list()
        data = list()

        for i in range(0, len(covid.index)):
            timestamp_total.append(timestamp[i])
            timestamp_total.append(total[i])
            data.append(timestamp_total)
            timestamp_total = list()

        country_data[k] = data
    #     print(country_name[k])

    # 하이차트 그리기
    france_series = {
        'name': 'France',
        'data': country_data[0],
        'color': '#7CCBA2'
    }
    germany_series = {
        'name': 'Germany',
        'data': country_data[1],
        'color': '#FCDE9C'
    }
    korea_series = {
        'name': 'Korea, South',
        'data': country_data[2],
        'color': '#045275'
    }
    us_series = {
        'name': 'US',
        'data': country_data[3],
        'color': '#DC3977'
    }
    uk_series = {
        'name': 'United Kingdom',
        'data': country_data[4],
        'color': '#7C1D6F'
    }

    chart = {
        'chart': {'type': 'line'},
        'title': {'text': 'COVID-19 확진자 회복률'},
        'subtitle': {'text': 'Source: Johns Hopkins university Center for System Science and Engineering'},
        'series': [france_series, germany_series, korea_series, us_series, uk_series],

        'xAxis': {
            'type': 'datetime',
            'labels': {
                'format': '{value:%b}'  # https://jsfiddle.net/dLfv2sbd/1/
            },
            'crosshair': 'true',
        },

        'yAxis': {
            'title': {
                'text': '회복률',
                'rotation': -90
            },
            'labels': {
                'enabled': 'false',
                'format': '{value}%'},
            'crosshair': 'true'
        },

        'responsive': {
            'rules': [{
                'condition': {
                    'maxWidth': 500
                },
            }]
        },

        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': 'false'
                },

            }
        },

    }
    dump = json.dumps(chart)

    return render(request, 'chart/covid19_chart_recovered.html', {'chart': dump})


def covid19_chart_deaths(request):
    # 데이터 적재 및 선별
    df = pd.read_csv('https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv',
                     parse_dates=['Date'])
    countries = ['Korea, South', 'Germany', 'United Kingdom', 'US', 'France']
    df = df[df['Country'].isin(countries)]

    # 데이터프레임 준비(회복자)
    dfd = df.pivot(index='Date', columns='Country', values='Deaths')
    # 데이터프레임 준비(확진자)
    dfc = df.pivot(index='Date', columns='Country', values='Confirmed')

    # 회복자 / 확진자 * 100 으로 회복율 구하기
    df = round((dfd / dfc) * 100, 2)

    # 인덱스 조작
    covid = df.reset_index('Date')
    covid.set_index(['Date'], inplace=True)
    covid.columns = countries

    # 날짜별 타임스탬프 값 구하기(arrow 사용)
    date = covid.index
    arrow_date = list()

    for d in date:
        arrow_date.append(arrow.get(d.year, d.month, d.day).timestamp * 1000)
        # http://doc.mindscale.kr/km/python/07.html

    # timestamp 열 추가
    covid['timestamp'] = arrow_date

    # timestamp 열로 인덱스 변경
    covid.reset_index('Date')
    covid.set_index(['timestamp'], inplace=True)
    covid.columns = countries

    # 하이차트 그리기 위해 2차원 배열로 데이터 생성
    # [[timestamp, total], [timestamp, total], ...]
    country_data = countries
    for k in range(0, len(countries)):
        #     print(country_data[k])
        timestamp = list(covid.index)
        total = list(covid[countries[k]])
        timestamp_total = list()
        data = list()

        for i in range(0, len(covid.index)):
            timestamp_total.append(timestamp[i])
            timestamp_total.append(total[i])
            data.append(timestamp_total)
            timestamp_total = list()

        country_data[k] = data
    #     print(country_name[k])

    # 하이차트 그리기
    france_series = {
        'name': 'France',
        'data': country_data[0],
        'color': '#7CCBA2'
    }
    germany_series = {
        'name': 'Germany',
        'data': country_data[1],
        'color': '#FCDE9C'
    }
    korea_series = {
        'name': 'Korea, South',
        'data': country_data[2],
        'color': '#045275'
    }
    us_series = {
        'name': 'US',
        'data': country_data[3],
        'color': '#DC3977'
    }
    uk_series = {
        'name': 'United Kingdom',
        'data': country_data[4],
        'color': '#7C1D6F'
    }

    chart = {
        'chart': {'type': 'line'},
        'title': {'text': 'COVID-19 확진자 사망률'},
        'subtitle': {'text': 'Source: Johns Hopkins university Center for System Science and Engineering'},
        'series': [france_series, germany_series, korea_series, us_series, uk_series],

        'xAxis': {
            'type': 'datetime',
            'labels': {
                'format': '{value:%b}'  # https://jsfiddle.net/dLfv2sbd/1/
            },
            'crosshair': 'true',
        },

        'yAxis': {
            'title': {
                'text': '사망률',
                'rotation': -90
            },
            'labels': {
                'enabled': 'false',
                'format': '{value}%'},
            'crosshair': 'true'
        },

        'responsive': {
            'rules': [{
                'condition': {
                    'maxWidth': 500
                },
            }]
        },

        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': 'false'
                },

            }
        },

    }
    dump = json.dumps(chart)

    return render(request, 'chart/covid19_chart_deaths.html', {'chart': dump})


# https://jsfiddle.net/gh/get/library/pure/highcharts/highcharts/tree/master/samples/highcharts/demo/combo-dual-axes/
def ticket_class_view_final(request):
    dataset = Passenger.objects \
        .values('ticket_class') \
        .annotate(survived_count=Count('ticket_class', filter=Q(survived=True)),
                  not_survived_count=Count('ticket_class', filter=Q(survived=False))) \
        .order_by('ticket_class')

    # 빈 리스트 3종 준비 (series 이름 뒤에 '_data' 추가)
    categories = list()  # for xAxis
    survived_series_data = list()  # for series named 'Survived'
    not_survived_series_data = list()  # for series named 'Not survived'
    survive_rate_data = list()

    # 리스트 3종에 형식화된 값을 등록
    for entry in dataset:
        categories.append('%s등석' % entry['ticket_class'])  # for xAxis
        survived_series_data.append(entry['survived_count'])  # for series named 'Survived'
        not_survived_series_data.append(entry['not_survived_count'])  # for series named 'Not survived'
        survive_rate_data.append(
            round(entry['survived_count'] / (entry['survived_count'] + entry['not_survived_count']) * 100, 2)
        )

    survived_series = {
        'type': 'column',
        'name': '생존',
        'data': survived_series_data,
        'color': 'green',
        'yAxis': 1,
        'tooltip': {
            'valueSuffix': '명'
        }
    }
    not_survived_series = {
        'type': 'column',
        'name': '비생존',
        'data': not_survived_series_data,
        'color': 'red',
        'yAxis': 1,
        'tooltip': {
            'valueSuffix': '명'
        }
    }
    survive_rate = {
        'type': 'line',
        'name': '생존율',
        'data': survive_rate_data,
        'tooltip': {
            'valueSuffix': '%'
        }
    }

    chart = {
        'title': {'text': '좌석 등급에 따른 타이타닉 생존/비생존 인원 및 생존율'},
        'xAxis': {'categories': categories},
        'yAxis': [{
            'tickPositions': [20, 30, 40, 50, 60, 70],
            'labels': {
                'format': '{value}%',
                'style': {
                    'color': '#0086c9'
                }
            },
            'title': {
                'text': '생존율',
                'style': {
                    'color': '#0086c9'
                }
            }
        }, {
            'tickPositions': [0, 120, 240, 360, 480, 600],
            'labels': {
                'format': '{value}명',
            },
            'title': {
                'text': '인원',
            },
            'opposite': 'true'
        }],
        'tooltip': {
            'shared': 'true'
        },
        'legend': {'layout': 'vertical',
                   'align': 'left',
                   'x': 120,
                   'verticalAlign': 'top',
                   'y': 100,
                   'floating': 'true',
        },
        'series': [survived_series, not_survived_series, survive_rate],

        'responsive': {
            'chartOptions': {
                'yAxis': [{
                    'labels': {
                        'align': 'right',
                    },
                    'labels': {
                        'align': 'left',
                    }
                }]
            }
        }
    }
    dump = json.dumps(chart)

    return render(request, 'chart/ticket_class_final.html', {'chart': dump})

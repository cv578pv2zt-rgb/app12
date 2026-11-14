"""장바구니 역설계 | Python 3.10+
GitHub에 app.py와 requirements.txt 업로드 → Streamlit Community Cloud에서 app.py 배포.
외부 API, 로그인, DB 불필요. 입력은 현재 세션에만 유지됩니다.
재료량·가격은 계산용 예시이며 실제 영양·시세·소비기한 정보가 아닙니다.
QR 공유는 배포 주소를 브라우저에서 QR로 공유하세요. 공용 상태 동기화는 지원하지 않습니다.
"""
import itertools
import math
import streamlit as st

# 재료: 구매 단위 수량, 단위, 포장 가격. 달걀은 개, 나머지는 g.
ING={
 '쌀':(1000,'g',4500),'달걀':(10,'개',4500),'두부':(300,'g',1800),
 '돼지고기':(500,'g',8000),'닭고기':(500,'g',6500),'양배추':(1000,'g',3500),
 '양파':(1000,'g',2800),'대파':(300,'g',2000),'감자':(1000,'g',4000),
 '당근':(500,'g',2000),'애호박':(300,'g',1800),'김치':(500,'g',5000),
 '참치':(150,'g',2200),'우동면':(400,'g',2400),'어묵':(300,'g',2400),
}
# 1인분 재료 사용량. 주식이 포함된 계산용 메뉴이며 실제 사용량은 취향에 따라 달라집니다.
REC={
 '김치볶음밥':{'쌀':90,'김치':100,'달걀':1,'대파':15},
 '달걀볶음밥':{'쌀':90,'달걀':2,'당근':30,'대파':15,'양파':40},
 '참치덮밥':{'쌀':90,'참치':75,'달걀':1,'양파':50},
 '두부김치 덮밥':{'쌀':90,'두부':150,'김치':100,'양파':40},
 '돼지고기 양배추덮밥':{'쌀':90,'돼지고기':120,'양배추':120,'양파':50},
 '닭고기덮밥':{'쌀':90,'닭고기':130,'달걀':1,'양파':60},
 '감자달걀 한상':{'쌀':90,'감자':150,'달걀':2,'대파':15},
 '두부채소 한상':{'쌀':90,'두부':150,'애호박':80,'당근':30,'양파':40},
 '닭고기 채소볶음밥':{'쌀':90,'닭고기':100,'양배추':80,'당근':30,'양파':40},
 '돼지고기 김치 한상':{'쌀':90,'돼지고기':120,'김치':120,'두부':80},
 '어묵볶음우동':{'우동면':200,'어묵':80,'양배추':120,'양파':50,'당근':20},
 '닭고기 볶음우동':{'우동면':200,'닭고기':100,'양배추':100,'양파':40},
 '참치김치 덮밥':{'쌀':90,'참치':75,'김치':100,'양파':40},
 '두부달걀 덮밥':{'쌀':90,'두부':100,'달걀':2,'양파':50},
}

def evaluate(menus,people,stock,prices,packs):
    need={k:0 for k in ING}
    for menu in menus:
        for k,v in REC[menu].items():need[k]+=v*people
    rows=[];total=0;surplus_value=0
    for k,n in need.items():
        if n==0:continue
        size=packs[k];price=prices[k];available=stock[k]
        missing=max(0,n-available)
        count=math.ceil(missing/size) if missing else 0
        extra=count*size-missing
        cost=count*price
        total+=cost
        surplus_value+=extra/size*price
        rows.append({'재료':k,'단위':ING[k][1],'필요량':n,'보유량':available,
                     '구매 포장':count,'구매량':count*size,'구매 후 잉여':extra,'금액':cost})
    return {'menus':menus,'rows':rows,'total':total,'surplus':surplus_value}

def optimize(candidates,meals,people,stock,prices,packs,budget,mode):
    results=[evaluate(c,people,stock,prices,packs) for c in itertools.combinations(candidates,meals)]
    # 예산 안 조합을 우선. 없으면 초과 금액이 가장 적은 조합부터.
    def key(r):
        excess=max(0,r['total']-budget)
        rest=(r['surplus'],r['total']) if mode=='남는 재료 줄이기' else (r['total'],r['surplus'])
        return (excess>0,excess,*rest)
    return sorted(results,key=key)[:3]

def main():
    st.set_page_config(page_title='장바구니 역설계',page_icon='🛒',layout='centered')
    st.markdown('''<style>
    .block-container{max-width:540px;padding-top:1.2rem;padding-bottom:2rem}
    h1{font-size:1.75rem!important;color:#164e48;text-align:center} [data-testid="stCaptionContainer"]{color:#64746e} div[data-testid="stMetricValue"]{font-size:1.5rem} div[data-testid="stForm"]{border:0;padding:0} [data-testid="stToolbar"]{visibility:hidden} .stButton button[kind="primary"]{background:#176b5b;border:0;min-height:48px}
    div[data-testid="stMetric"]{background:#f0f6f3;border-radius:12px;padding:12px}
    @media(max-width:600px){.block-container{padding-left:1rem;padding-right:1rem}h1{font-size:1.55rem!important}}
    </style>''',unsafe_allow_html=True)
    st.title('🛒 장바구니 역설계')
    st.markdown('<p style="text-align:center;color:#64746e;font-size:14px">장보기 예상 금액과 사고 남는 재료를 확인해요</p>',unsafe_allow_html=True)
    st.info('① 인원·끼니 입력 → ② 집에 있는 재료 입력 → ③ 계산하기')
    st.caption('선택한 메뉴 후보에서 식단을 추천하고, 포장 단위로 살 때의 예상 금액과 남는 양을 계산합니다.')
    with st.container():
        a,b=st.columns(2)
        people=a.number_input('① 몇 명이 먹나요?',1,8,3)
        meals=b.number_input('몇 끼를 준비하나요?',1,5,3)
        budget=st.number_input('장보기 예산은 얼마인가요? (원)',0,500000,40000,step=1000)
        with st.expander('선택 설정 · 우선순위와 제외 재료'):
            mode=st.radio('우선순위',['장보기 비용 줄이기','남는 재료 줄이기'],horizontal=True)
            excluded=st.multiselect('빼고 싶은 재료',list(ING),help='알레르기 안전 판정이 아닙니다. 양념과 교차접촉은 별도로 확인하세요.')
        with st.expander('② 집에 있는 재료 입력 · 가격 수정', expanded=True):
            st.caption('집에 있는 재료를 선택하고 양을 적으세요. 모르면 0으로 두세요. 가격은 실시간 가격이 아닌 예시입니다.')
            available=st.multiselect('집에 무엇이 있나요?',list(ING),placeholder='예: 쌀, 달걀, 양파')
            stock_inputs={}
            for k in available:
                stock_inputs[k]=st.number_input(f'{k} 보유량 ({ING[k][1]})',min_value=0,step=1,key='stock_'+k)
            st.caption('기본 가격으로 먼저 계산해도 됩니다. 정확하게 보려면 아래에서 가격을 바꾸세요.')
            with st.expander('마트 포장 크기·가격 바꾸기'):
                base=[{'재료':k,'단위':v[1],'포장량':v[0],'포장가격':v[2]} for k,v in ING.items()]
                edited=st.data_editor(base,hide_index=True,use_container_width=True,disabled=['재료','단위'],
                    column_config={c:st.column_config.NumberColumn(c,min_value=(1 if c=='포장량' else 0),step=1,required=True) for c in ['포장량','포장가격']})
        with st.expander('메뉴 후보 바꾸기'):
            candidates=st.multiselect('원하는 메뉴만 후보로 넣기',list(REC),default=list(REC))
        submitted=st.button('③ 예상 금액 · 남는 재료 보기',type='primary',use_container_width=True)
    if submitted:
        stock={};prices={};packs={}
        try:
            for row in edited:
                k=row['재료'];stock[k]=int(stock_inputs.get(k,0));prices[k]=int(row['포장가격']);packs[k]=int(row['포장량'])
                if stock[k]<0 or prices[k]<0 or packs[k]<=0:raise ValueError()
        except (TypeError,ValueError):
            st.error('보유량·가격은 0 이상, 포장량은 1 이상인 정수로 입력하세요.');return
        allowed=[m for m in candidates if not set(REC[m]).intersection(excluded)]
        if len(allowed)<meals:
            st.warning('조건에 맞는 서로 다른 메뉴가 부족해요. 제외 재료를 줄이거나 끼니 수를 낮춰주세요.');return
        with st.spinner('메뉴 조합과 포장 수량을 비교하고 있어요…'):
            st.session_state['plans']=optimize(allowed,meals,people,stock,prices,packs,budget,mode)
            st.session_state['budget']=budget
        st.session_state['choice']=0
    plans=st.session_state.get('plans')
    if plans:
        st.divider()
        st.caption('계산 결과 · 조건을 바꾸면 다시 계산해 주세요.')
        choice=st.selectbox('장바구니 대안',range(len(plans)),key='choice',format_func=lambda i:f"{'추천' if i==0 else '대안 '+str(i)} · {plans[i]['total']:,}원")
        r=plans[choice];a,b=st.columns(2)
        a.metric('예상 장보기 금액',f"{r['total']:,}원")
        diff=st.session_state['budget']-r['total']
        b.metric('예산 잔액' if diff>=0 else '예산 초과',f'{abs(diff):,}원')
        if diff<0:st.warning('이 조건에서는 예산 안 조합이 없습니다. 비교한 후보 중 초과 금액이 적은 안입니다.')
        st.markdown('#### 🍽️ 식단')
        for i,menu in enumerate(r['menus'],1):st.write(f'{i}. **{menu}**')
        st.markdown('#### 🛒 장보기')
        buy=[x for x in r['rows'] if x['구매 포장']]
        lines=['장바구니 역설계','식단: '+', '.join(r['menus']),'']
        for row in buy:
            desc=f"{row['재료']} · {row['구매 포장']}포장 ({row['구매량']}{row['단위']}) · {row['금액']:,}원"
            st.checkbox(desc,key=f"buy_{choice}_{desc}")
            lines.append('□ '+desc)
        if not buy:st.success('입력한 보유 재료만으로 준비할 수 있어요.')
        lines.append(f"\n총 구매액: {r['total']:,}원")
        st.download_button('장보기 목록 저장','\n'.join(lines).encode('utf-8-sig'),'장보기목록.txt','text/plain',use_container_width=True)
        st.markdown('#### 🥬 사고 남는 재료')
        leftovers=[x for x in r['rows'] if x['구매 후 잉여']>0]
        if leftovers:
            for row in leftovers:
                st.write(f"• **{row['재료']}** {row['구매 후 잉여']}{row['단위']}")
        else:
            st.success('새로 산 재료는 계산상 남지 않아요.')
        st.caption('위 잔량은 새로 산 재료 중 식단에 쓰고 남는 양입니다. 기존 보유 재료의 잔량은 제외합니다.')
        with st.expander('자세한 계산 보기'):
            st.dataframe(r['rows'],hide_index=True,use_container_width=True)
            st.caption('구매 후 잉여 = 새로 산 양 중 사용하고 남는 양. 기존 보유분의 잔량은 포함하지 않습니다. 잉여 최소화는 g·개를 직접 더하지 않고 포장 가격으로 환산한 금액을 비교합니다.')
        with st.expander('메뉴별 재료 확인'):
            for menu in r['menus']:
                st.write('**'+menu+' · 1인분 기준**')
                st.write(' / '.join(f'{k} {v}{ING[k][1]}' for k,v in REC[menu].items()))
    with st.expander('이용 안내'):
        st.caption('가격은 직접 수정 가능한 예시입니다. 밥 메뉴는 생쌀 기준이며 물·식용유·소금·간장·설탕 등 기본양념과 에너지 비용은 제외됩니다. 전체 식비·영양 균형을 보장하지 않습니다. 재료 보관 상태와 제품 표시를 별도로 확인하세요. 입력은 현재 세션에만 유지되며 가족 간 실시간 동기화는 지원하지 않습니다.')

if __name__=='__main__':main()

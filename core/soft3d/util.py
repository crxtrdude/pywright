def trans(q,x=0,y=0,z=0):
    for p in q.points[:4]:
        p[0]+=x
        p[1]+=y
        p[2]+=z
def push(q,z=0):
    q.points[0][2]+=z
    q.points[3][2]+=z
def uvscroll(q,u=0,v=0):
    for p in q.points[:4]:
        p[3]+=u
        p[4]+=v
def scale(q,amt):
    for p in q.points[:4]:
        p[0]*=amt
        p[1]*=amt
        p[2]*=amt
def get_center(quads):
    lx=1000
    rx=-1000
    ly=1000
    ry=-1000
    lz=1000
    rz=-1000
    for q in quads:
        for p in q.points:
            if p[0]<lx:
                lx=p[0]
            if p[0]>rx:
                rx=p[0]
            if p[1]<ly:
                ly=p[1]
            if p[1]>ry:
                ry=p[1]
            if p[2]<lz:
                lz=p[2]
            if p[2]>rz:
                rz=p[2]
    return [lx+(rx-lx)/2.,ly+(ry-ly)/2.,lz+(rz-lz)/2.]
// 渲染 Markdown 内容
document.querySelectorAll('.summary-text').forEach((element) => {
    element.innerHTML = marked.parse(element.textContent);
});

// 右侧目录跟随滚动
document.addEventListener('DOMContentLoaded', function () {
    const sections = document.querySelectorAll('.content-main h3');
    const menuLinks = document.querySelectorAll('.menu-list a');
    const sidebar = document.querySelector('.content-sidebar');

    const makeActive = (link) => menuLinks[link].classList.add("is-active");
    const removeActive = (link) => menuLinks[link].classList.remove("is-active");
    const removeAllActive = () => [...Array(sections.length).keys()].forEach((link) => removeActive(link));

    let currentActive = 0;

    window.addEventListener('scroll', () => {
        const windowMidpoint = window.scrollY + window.innerHeight / 2;

        let closestSectionIndex = 0;
        let closestDistance = Infinity;

        sections.forEach((section, index) => {
            const sectionMidpoint = section.offsetTop + section.offsetHeight / 2;
            const distance = Math.abs(sectionMidpoint - windowMidpoint);

            if (distance < closestDistance) {
                closestDistance = distance;
                closestSectionIndex = index;
            }
        });

        if (closestSectionIndex !== currentActive) {
            removeAllActive();
            currentActive = closestSectionIndex;
            makeActive(currentActive);

            // 获取活跃目录项及其相对于sidebar的位置
            const activeElement = menuLinks[currentActive];
            if (activeElement) {
                const activeElementOffset = activeElement.offsetTop;
                const sidebarHeight = sidebar.offsetHeight;

                // 判断活跃目录项是否超出sidebar的可见范围
                if (activeElementOffset > sidebar.scrollTop + sidebarHeight || activeElementOffset < sidebar.scrollTop) {
                    // 将活跃目录项滚动到sidebar的中央位置
                    sidebar.scrollTop = activeElementOffset - sidebarHeight / 2 - activeElement.offsetHeight / 2;
                }
            }
        }
    });
});
/**
 * 测试API获取PKX数据
 */

async function testAPI() {
  console.log('========================================');
  console.log('测试 PKX 航班预测 API');
  console.log('========================================');
  console.log();

  try {
    const response = await fetch('http://localhost:6001/api/airport/prediction');
    const data = await response.json();

    if (data.success && data.data.airports) {
      // 查找PKX
      const pkx = data.data.airports.find((a: any) => a.code === 'PKX');

      if (pkx) {
        console.log('✓ PKX 数据存在');
        console.log(`  名称: ${pkx.name}`);
        console.log(`  状态: ${pkx.status}`);
        console.log();

        if (pkx.terminals && pkx.terminals.length > 0) {
          console.log(`  航站楼数量: ${pkx.terminals.length}`);
          console.log();

          pkx.terminals.forEach((terminal: any) => {
            console.log(`  航站楼: ${terminal.name}`);
            console.log(`  总计3小时: ${terminal.total3Hours}`);
            console.log(`  推荐: ${terminal.recommendation}`);
            console.log();

            console.log('  小时明细:');
            terminal.hourlyBreakdown.forEach((hour: any) => {
              console.log(`    ${hour.timeRange}: ${hour.plannedCount}架`);
            });
            console.log();
          });
        }
      } else {
        console.log('✗ 未找到 PKX 数据');
      }

      // 显示汇总
      console.log('========================================');
      console.log('汇总数据');
      console.log('========================================');
      console.log(`当前时间: ${data.data.currentTime}`);
      console.log(`预测时段: ${data.data.predictionPeriod}`);
      console.log(`最热机场: ${data.data.summary.hottestAirport}`);
      console.log(`最热航站楼: ${data.data.summary.hottestTerminal}`);
      console.log();

    } else {
      console.log('✗ API 返回格式错误');
    }

  } catch (error: any) {
    console.error('✗ 请求失败:', error.message);
  }
}

testAPI();
